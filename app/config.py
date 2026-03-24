"""
Application configuration via Pydantic Settings.
Reads from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the Stock Intelligence Platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── PostgreSQL ────────────────────────────────────
    database_url: str = "postgresql+asyncpg://stockadmin:stockpass123@localhost:5432/stockintel"

    # ── MongoDB ───────────────────────────────────────
    mongo_url: str = "mongodb://mongoadmin:mongopass123@localhost:27017"
    mongo_db_name: str = "stockintel"

    # ── Redis ─────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Scraper ───────────────────────────────────────
    nse_rate_limit: int = 5
    scraper_max_retries: int = 3

    # ── RBI ───────────────────────────────────────────
    rbi_bulletin_url: str = "https://www.rbi.org.in/Scripts/BS_ViewBulletin.aspx"

    # ── FRED / GPR ────────────────────────────────────
    fred_api_key: str = ""
    gpr_cache_ttl: int = 21600  # 6 hours in seconds

    # ── Celery ────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ── FinBERT / NLP ────────────────────────────────
    finbert_model_name: str = "ProsusAI/finbert"
    finbert_batch_size: int = 32

    # ── Sentiment ─────────────────────────────────────
    sentiment_decay_lambda: float = 0.2
    sentiment_window_days: int = 7
    news_cache_ttl: int = 1800  # 30 min

    # ── Selenium ──────────────────────────────────────
    selenium_headless: bool = True

    # ── App ───────────────────────────────────────────
    app_name: str = "Indian Stock Intelligence Platform"
    debug: bool = False


settings = Settings()
