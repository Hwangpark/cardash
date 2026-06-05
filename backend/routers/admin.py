from typing import Optional

from fastapi import APIRouter, BackgroundTasks

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/crawl")
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    platform: Optional[str] = None,
):
    from crawlers.encar import EncarCrawler

    crawlers = {"encar": EncarCrawler}

    targets = [crawlers[platform]] if platform and platform in crawlers else list(crawlers.values())

    async def run():
        for CrawlerClass in targets:
            crawler = CrawlerClass()
            await crawler.run()

    background_tasks.add_task(run)
    return {"status": "started", "platforms": [c.__name__ for c in targets]}
