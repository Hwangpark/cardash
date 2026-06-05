from .bobaedream import BobaedreamCrawler
from .encar import EncarCrawler
from .kbchachacha import KbchachachaCrawler
from .kcar import KcarCrawler

CRAWLERS: dict[str, type] = {
    "encar": EncarCrawler,
    "kcar": KcarCrawler,
    "kbchachacha": KbchachachaCrawler,
    "bobaedream": BobaedreamCrawler,
}

__all__ = ["EncarCrawler", "KcarCrawler", "KbchachachaCrawler", "BobaedreamCrawler", "CRAWLERS"]
