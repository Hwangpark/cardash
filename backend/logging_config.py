"""파일 로깅 설정 — 분석기의 보험이력 fetch 실패 사유를 로그 파일로 남긴다."""
import logging
from pathlib import Path

LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "app.log"


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)

    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    ))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
