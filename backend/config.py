from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://cardash:cardash1234@localhost:5433/cardash"
    redis_url: str = "redis://localhost:6379/0"
    crawl_interval_hours: int = 6
    # 운영 환경에서는 .env의 ADMIN_TOKEN으로 재정의할 것
    admin_token: str = "dev-admin-token"

    class Config:
        env_file = ".env"


settings = Settings()
