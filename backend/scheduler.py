"""미채점 차량 백그라운드 채점 스케줄러"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import AsyncSessionLocal
from services.scorer import score_unscored_batch

SCORE_BATCH_SIZE = 25
SCORE_INTERVAL_MINUTES = 10

_scheduler = AsyncIOScheduler()


async def _run_scoring_batch():
    async with AsyncSessionLocal() as db:
        scored = await score_unscored_batch(db, limit=SCORE_BATCH_SIZE)
        if scored:
            print(f"[scheduler] scored {scored} cars")


def start_scheduler():
    _scheduler.add_job(
        _run_scoring_batch,
        trigger=IntervalTrigger(minutes=SCORE_INTERVAL_MINUTES),
        id="score_unscored_cars",
        max_instances=1,
        replace_existing=True,
    )
    _scheduler.start()


def shutdown_scheduler():
    _scheduler.shutdown(wait=False)
