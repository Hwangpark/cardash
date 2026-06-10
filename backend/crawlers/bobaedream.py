import re
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from crawlers.base import BaseCrawler

BASE_URL = "https://www.bobaedream.co.kr"
LIST_URL = f"{BASE_URL}/cyber/CyberCar.php"
IMG_BASE = "https:"

# 국산/수입 구분 (gubun)
GUBUN_LIST = ["K", "I"]

# (브랜드명, 모델그룹명) → 보배드림 maker_no/group_no
CATEGORY_CODES = {
    ("제네시스", "G70"): {"maker_no": "1010", "group_no": "935"},
}

KNOWN_BRANDS = {
    "현대", "기아", "제네시스", "쌍용", "쉐보레", "대우", "르노", "삼성",
    "BMW", "벤츠", "아우디", "폭스바겐", "포르쉐", "볼보", "미니", "렉서스",
    "토요타", "혼다", "닛산", "인피니티", "마쓰다", "미쓰비시", "스바루",
    "포드", "지프", "링컨", "캐딜락", "크라이슬러", "GMC", "테슬라",
    "랜드로버", "재규어", "푸조", "시트로앵", "DS", "피아트", "알파로메오",
    "마세라티", "페라리", "람보르기니", "벤틀리", "롤스로이스",
}


class BobaedreamCrawler(BaseCrawler):
    PLATFORM = "bobaedream"
    DELAY_MIN = 4.0
    DELAY_MAX = 7.0

    async def fetch_list(self, page: int, category: dict[str, Any] | None = None) -> list[dict]:
        codes = self._category_codes(category)
        gubuns = ["K"] if codes else GUBUN_LIST

        results = []
        for gubun in gubuns:
            params = {"gubun": gubun, "page": page, **codes} if codes else {"gubun": gubun, "page": page}
            html = await self.get_html(LIST_URL, params=params)
            if html:
                results.extend(self._parse_list(html, gubun))
        return results

    def _category_codes(self, category: dict[str, Any] | None) -> dict[str, str] | None:
        if not category:
            return None
        key = (category.get("make_code"), category.get("model_group_code"))
        return CATEGORY_CODES.get(key)

    async def fetch_detail(self, external_id: str) -> dict:
        return {}  # 리스트에서 충분한 정보 수집

    async def normalize(self, raw: dict, category: dict[str, Any] | None = None) -> dict:
        if not raw.get("external_id"):
            return {}

        title = raw.get("title", "")
        brand, model = self._split_brand_model(title)

        return {
            "platform": self.PLATFORM,
            "external_id": raw["external_id"],
            "brand": brand,
            "model_group": model.split()[0] if model else None,
            "model": model,
            "year": raw.get("year"),
            "price": raw.get("price"),
            "mileage": raw.get("mileage"),
            "region": raw.get("region"),
            "fuel": raw.get("fuel"),
            "transmission": raw.get("transmission"),
            "color": None,
            "seller_type": "private",
            "images": raw.get("images", []),
            "url": raw.get("url"),
            "raw_data": raw,
        }

    # ── HTML 파싱 ──────────────────────────────────────

    def _parse_list(self, html: str, gubun: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        # 상세 페이지 링크로 차량 ID 추출 (href=CyberCar_view.php?no=...)
        seen = set()
        for link in soup.find_all("a", href=re.compile(r"CyberCar_view\.php\?no=\d+")):
            car_no = self._extract_no(link["href"])
            if not car_no or car_no in seen:
                continue
            seen.add(car_no)

            container = self._find_container(link)
            if not container:
                continue

            item = self._extract_item(container, car_no, gubun, link["href"])
            if item:
                results.append(item)

        return results

    def _extract_no(self, href: str) -> str | None:
        params = parse_qs(urlparse(href).query)
        nos = params.get("no", [])
        return nos[0] if nos else None

    def _find_container(self, link: Tag) -> Tag | None:
        for tag in ("li", "div", "tr"):
            parent = link.find_parent(tag)
            if parent:
                return parent
        return link.parent

    def _extract_item(self, el: Tag, car_no: str, gubun: str, href: str) -> dict | None:
        text_parts = el.get_text(" ", strip=True)
        title = self._extract_title(el)
        if not title:
            return None

        return {
            "external_id": f"{gubun}_{car_no}",
            "title": title,
            "price": self._parse_price(text_parts),
            "mileage": self._parse_mileage(text_parts),
            "year": self._parse_year(text_parts),
            "region": self._parse_region(el, text_parts),
            "fuel": self._parse_fuel(text_parts),
            "transmission": self._parse_transmission(text_parts),
            "images": self._extract_images(el),
            "url": urljoin(BASE_URL, href),
        }

    def _extract_title(self, el: Tag) -> str | None:
        # bobaedream: <p class="tit ellipsis"><a title="차량명">...</a></p>
        tit = el.find("p", class_=re.compile(r"\btit\b"))
        if tit:
            a = tit.find("a")
            if a:
                return a.get("title") or a.get_text(strip=True) or None
        for a_tag in el.find_all("a"):
            t = a_tag.get("title", "").strip()
            if t and len(t) > 3:
                return t
        return None

    def _parse_price(self, text: str) -> int | None:
        m = re.search(r"([\d,]+)\s*만원", text)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    def _parse_mileage(self, text: str) -> int | None:
        m = re.search(r"([\d.]+)\s*만\s*km", text, re.IGNORECASE)
        if m:
            try:
                return int(float(m.group(1)) * 10000)
            except ValueError:
                return None
        m2 = re.search(r"([\d,]+)\s*km", text, re.IGNORECASE)
        if m2:
            try:
                return int(m2.group(1).replace(",", ""))
            except ValueError:
                return None
        return None

    def _parse_year(self, text: str) -> int | None:
        # "18/01" 또는 "2018년" 패턴
        m = re.search(r"\b(\d{2})/\d{2}\b", text)
        if m:
            yy = int(m.group(1))
            return 2000 + yy if yy < 50 else 1900 + yy
        m2 = re.search(r"\b(20\d{2})\b", text)
        if m2:
            return int(m2.group(1))
        return None

    def _parse_region(self, el: Tag, text: str) -> str | None:
        regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산",
                   "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
        for r in regions:
            if r in text:
                return r
        return None

    def _parse_fuel(self, text: str) -> str | None:
        for fuel in ["가솔린", "디젤", "LPG", "하이브리드", "전기", "수소"]:
            if fuel in text:
                return fuel
        return None

    def _parse_transmission(self, text: str) -> str | None:
        if "자동" in text:
            return "자동"
        if "수동" in text:
            return "수동"
        return None

    def _extract_images(self, el: Tag) -> list[str]:
        imgs = []
        for img in el.find_all("img"):
            src = img.get("src", "")
            if "bobaedream" in src or "CyberCar" in src:
                if src.startswith("//"):
                    src = "https:" + src
                imgs.append(src)
        return imgs

    def _split_brand_model(self, title: str) -> tuple[str | None, str | None]:
        if not title:
            return None, None
        parts = title.split()
        if not parts:
            return None, None
        # 첫 단어가 알려진 브랜드면 분리
        if parts[0] in KNOWN_BRANDS:
            brand = parts[0]
            model = " ".join(parts[1:]) if len(parts) > 1 else None
            return brand, model
        return None, title
