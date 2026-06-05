from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cardash:cardash1234@localhost:5433/cardash"
    redis_url: str = "redis://localhost:6379/0"
    crawl_interval_hours: int = 6

    class Config:
        env_file = ".env"


settings = Settings()
