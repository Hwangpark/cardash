"""KB차차차 크롤러 — 검색 결과 HTML(list.empty) 파싱"""
import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from crawlers.base import BaseCrawler

BASE_URL = "https://www.kbchachacha.com"
LIST_URL = f"{BASE_URL}/public/search/list.empty"

# (브랜드명, 모델그룹명) → KB차차차 makerCode/classCode
CATEGORY_CODES = {
    ("제네시스", "G70"): {"make_code": "189", "model_group_code": "2698"},
}


class KbchachachaCrawler(BaseCrawler):
    PLATFORM = "kbchachacha"
    DELAY_MIN = 4.0
    DELAY_MAX = 7.0

    async def fetch_list(self, page: int, category: dict[str, Any] | None = None) -> list[dict]:
        params: dict[str, Any] = {"page": page}
        codes = self._category_codes(category)
        if codes:
            params["makerCode"] = codes["make_code"]
            params["classCode"] = codes["model_group_code"]

        html = await self.get_html(LIST_URL, params=params)
        if not html:
            return []
        return self._parse_list(html)

    def _category_codes(self, category: dict | None) -> dict[str, str] | None:
        if not category:
            return None
        key = (category.get("make_code"), category.get("model_group_code"))
        return CATEGORY_CODES.get(key)

    async def fetch_detail(self, external_id: str) -> dict:
        return {}  # 리스트에서 충분한 정보 수집

    async def normalize(self, raw: dict, category: dict[str, Any] | None = None) -> dict:
        car_seq = raw.get("car_seq")
        if not car_seq:
            return {}

        brand, model_group, model = self._split_title(raw.get("title", ""), category)

        return {
            "platform": self.PLATFORM,
            "external_id": car_seq,
            "brand": brand,
            "model_group": model_group,
            "model": model,
            "year": raw.get("year"),
            "trim": None,
            "price": raw.get("price"),
            "mileage": raw.get("mileage"),
            "fuel": None,
            "transmission": None,
            "color": None,
            "region": raw.get("region"),
            "seller_type": "dealer",
            "images": [raw["image"]] if raw.get("image") else [],
            "url": f"{BASE_URL}{raw['href']}" if raw.get("href") else None,
            "raw_data": raw,
        }

    # ── HTML 파싱 ──────────────────────────────────────

    def _parse_list(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        for el in soup.find_all("div", attrs={"data-car-seq": True}):
            item = self._extract_item(el)
            if item:
                results.append(item)
        return results

    def _extract_item(self, el: Tag) -> dict | None:
        car_seq = el.get("data-car-seq")
        title_tag = el.find("strong", class_="tit")
        title = title_tag.get_text(strip=True) if title_tag else None
        if not car_seq or not title:
            return None

        data_line = el.find("div", class_="data-line")
        spans = [s.get_text(strip=True) for s in data_line.find_all("span")] if data_line else []

        price_tag = el.find("span", class_="price")
        img_tag = el.select_one(".thumnail img")
        link_tag = el.find("a", href=re.compile(r"detail\.kbc\?carSeq="))

        return {
            "car_seq": car_seq,
            "title": title,
            "year": self._parse_year(spans[0]) if len(spans) > 0 else None,
            "mileage": self._parse_mileage(spans[1]) if len(spans) > 1 else None,
            "region": spans[2] if len(spans) > 2 else None,
            "price": self._parse_price(price_tag.get_text(strip=True) if price_tag else None),
            "image": img_tag.get("src") if img_tag else None,
            "href": link_tag.get("href") if link_tag else None,
        }

    def _split_title(self, title: str, category: dict | None) -> tuple[str | None, str | None, str | None]:
        if not title:
            return None, None, None
        parts = title.split()
        brand = parts[0] if parts else None

        codes = self._category_codes(category)
        if codes:
            model_group = category.get("model_group_code")
            model = title[len(brand):].strip() if brand else title
            return brand, model_group, model

        model_group = parts[1] if len(parts) > 1 else None
        model = " ".join(parts[1:]) if len(parts) > 1 else None
        return brand, model_group, model

    def _parse_year(self, text: str) -> int | None:
        m = re.search(r"(\d{2})/\d{2}", text)
        if not m:
            return None
        yy = int(m.group(1))
        return 2000 + yy if yy < 50 else 1900 + yy

    def _parse_mileage(self, text: str) -> int | None:
        m = re.search(r"([\d,]+)\s*km", text, re.IGNORECASE)
        if not m:
            return None
        return int(m.group(1).replace(",", ""))

    def _parse_price(self, text: str | None) -> int | None:
        if not text:
            return None
        m = re.search(r"([\d,]+)", text)
        if not m:
            return None
        return int(m.group(1).replace(",", ""))
