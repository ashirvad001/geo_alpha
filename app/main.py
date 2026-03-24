"""
Indian Stock Intelligence Platform — FastAPI Application Entry Point.

Features:
- Lifespan context manager for startup/shutdown
- CORS middleware
- Health check endpoint
- Mounted API routers
- APScheduler for automated jobs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import close_mongo, close_redis, engine, get_mongo_db, get_redis
from app.jobs.scheduler import start_scheduler, stop_scheduler
from app.models.schemas import HealthCheck
from app.routers import data, gpr, rbi, sentiment, stocks

# ── Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("🚀 Starting Indian Stock Intelligence Platform...")

    # Verify database connections
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ PostgreSQL connection OK")
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")

    try:
        mongo_db = get_mongo_db()
        await mongo_db.command("ping")
        logger.info("✅ MongoDB connection OK")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed: {e}")

    try:
        redis_client = get_redis()
        await redis_client.ping()
        logger.info("✅ Redis connection OK")
    except Exception as e:
        logger.warning(f"⚠️  Redis connection failed: {e}")

    # Start scheduler
    start_scheduler()
    logger.info("✅ APScheduler started")

    yield  # ── Application is running ──

    # Shutdown
    logger.info("🛑 Shutting down...")
    stop_scheduler()
    await close_mongo()
    await close_redis()
    await engine.dispose()
    logger.info("👋 Shutdown complete")


# ── Need to import text for health check query ───────
from sqlalchemy import text  # noqa: E402

# ── Application ──────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description=(
        "Production-ready backend for Nifty 50 stock data, "
        "RBI macro indicators, risk analytics, and news intelligence."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────
app.include_router(stocks.router)
app.include_router(rbi.router)
app.include_router(data.router)
app.include_router(gpr.router)
app.include_router(sentiment.router)


# ── Health Check ──────────────────────────────────────
@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """System health check – verifies connectivity to all backends."""
    result = HealthCheck()

    # PostgreSQL
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        result.postgres = "connected"
    except Exception:
        result.postgres = "disconnected"

    # MongoDB
    try:
        mongo_db = get_mongo_db()
        await mongo_db.command("ping")
        result.mongo = "connected"
    except Exception:
        result.mongo = "disconnected"

    # Redis
    try:
        redis_client = get_redis()
        await redis_client.ping()
        result.redis = "connected"
    except Exception:
        result.redis = "disconnected"

    # Overall status
    all_ok = all(
        s == "connected"
        for s in [result.postgres, result.mongo, result.redis]
    )
    result.status = "ok" if all_ok else "degraded"

    return result


@app.get("/", tags=["System"])
async def root():
    """Root endpoint — API info."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "stocks": "/api/stocks",
            "stock_history": "/api/stocks/{symbol}/history",
            "rbi_latest": "/api/rbi/latest",
            "data_refresh": "/api/data/refresh",
            "gpr_stock": "/api/gpr/stock/{symbol}",
            "gpr_heatmap": "/api/gpr/heatmap",
            "gpr_refresh": "/api/gpr/refresh",
            "sentiment": "/api/sentiment/{symbol}",
            "news_feed": "/api/news/feed",
            "news_refresh": "/api/news/refresh",
        },
    }
