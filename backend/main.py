from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine
from models import Car, PriceHistory, Score, VehicleCategory  # noqa: F401 — Alembic 인식용
from database import Base
from routers import admin, cars


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="CardDash API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 개발 환경 — 포트 변경 무관하게 허용
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cars.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
