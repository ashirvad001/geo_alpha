"""
Sentiment & News API router.

Endpoints:
- GET  /api/sentiment/{symbol} — current decayed sentiment score + trend
- GET  /api/news/feed          — latest 20 news articles with sentiment scores
- POST /api/news/refresh       — trigger async re-scrape + processing
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.database import get_redis
from app.models.schemas import (
    NewsFeedItem,
    NewsFeedResponse,
    NewsRefreshResponse,
    SentimentResponse,
    SentimentScoreOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sentiment & News"])

CACHE_TTL = settings.news_cache_ttl  # 30 min


def _serialize_datetime(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# ═══════════════════════════════════════════════════════
# GET /api/sentiment/{symbol}
# ═══════════════════════════════════════════════════════

@router.get("/api/sentiment/{symbol}", response_model=SentimentResponse)
async def get_sentiment(symbol: str):
    """
    Get current decayed sentiment score and trend for a stock.

    - **symbol**: NSE symbol (e.g., RELIANCE.NS)

    Returns composite sentiment score (7-day rolling, exponentially decayed),
    sentiment breakdown (positive/negative/neutral percentages), article count,
    and trend direction (bullish/bearish/neutral).
    """
    symbol = symbol.upper()
    if not symbol.endswith(".NS"):
        symbol = f"{symbol}.NS"

    # ── Check Redis cache ─────────────────────────────
    cache_key = f"sentiment:{symbol}"
    try:
        redis = get_redis()
        cached = await redis.get(cache_key)
        if cached:
            logger.debug(f"Cache HIT for {cache_key}")
            data = json.loads(cached)
            return SentimentResponse(**data)
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")

    # ── Compute rolling sentiment ─────────────────────
    from app.nlp.sentiment_aggregator import compute_rolling_sentiment
    from app.nlp.ticker_map import get_all_symbols, get_symbol_name

    if symbol not in get_all_symbols():
        raise HTTPException(
            status_code=404,
            detail=f"Symbol '{symbol}' not found in Nifty 50. Use NSE format (e.g., RELIANCE.NS).",
        )

    result = await compute_rolling_sentiment(symbol)

    response = SentimentResponse(
        symbol=symbol,
        name=get_symbol_name(symbol) or symbol,
        sentiment=SentimentScoreOut(
            composite_score=result["composite_score"],
            positive_pct=result["positive_pct"],
            negative_pct=result["negative_pct"],
            neutral_pct=result["neutral_pct"],
            article_count=result["article_count"],
            trend=result["trend"],
            window_days=result["window_days"],
            last_updated=result["last_updated"],
        ),
    )

    # ── Cache response ────────────────────────────────
    try:
        redis = get_redis()
        await redis.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(response.model_dump(), default=_serialize_datetime),
        )
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")

    return response


# ═══════════════════════════════════════════════════════
# GET /api/news/feed
# ═══════════════════════════════════════════════════════

@router.get("/api/news/feed", response_model=NewsFeedResponse)
async def get_news_feed(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Articles per page"),
    symbol: str | None = Query(None, description="Filter by NSE symbol"),
):
    """
    Get latest news articles with sentiment scores.

    Returns paginated list of recent financial news articles,
    each with FinBERT sentiment probabilities and stock mentions.
    """
    from app.database import get_mongo_db

    db = get_mongo_db()
    collection = db["raw_news_articles"]

    # Build query
    query: dict = {"processed": True, "sentiment": {"$ne": None}}
    if symbol:
        symbol = symbol.upper()
        if not symbol.endswith(".NS"):
            symbol = f"{symbol}.NS"
        query["stock_mentions"] = symbol

    # Count total
    total = await collection.count_documents(query)

    # Fetch paginated results
    skip = (page - 1) * page_size
    cursor = (
        collection.find(query)
        .sort("scraped_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    articles = await cursor.to_list(length=page_size)

    # Build response items
    items: list[NewsFeedItem] = []
    for art in articles:
        sent = art.get("sentiment", {})
        items.append(
            NewsFeedItem(
                headline=art.get("title", ""),
                summary=(art.get("body", "") or "")[:500],
                source=art.get("source", ""),
                source_url=art.get("url", ""),
                published_at=art.get("publish_time"),
                sentiment_score=sent.get("composite_score"),
                positive=sent.get("positive"),
                negative=sent.get("negative"),
                neutral=sent.get("neutral"),
                sentiment_label=sent.get("label"),
                stock_mentions=art.get("stock_mentions", []),
            )
        )

    return NewsFeedResponse(
        articles=items,
        count=len(items),
        total=total,
        page=page,
        page_size=page_size,
    )


# ═══════════════════════════════════════════════════════
# POST /api/news/refresh
# ═══════════════════════════════════════════════════════

@router.post("/api/news/refresh", response_model=NewsRefreshResponse)
async def refresh_news():
    """
    Trigger an async re-scrape and sentiment processing pipeline.

    Dispatches a Celery task and returns the task ID immediately.
    """
    try:
        from app.celery_app import celery_app

        task = celery_app.send_task(
            "app.tasks.sentiment_tasks.task_full_pipeline",
        )

        # Invalidate sentiment caches
        try:
            redis = get_redis()
            keys = await redis.keys("sentiment:*")
            if keys:
                await redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} sentiment cache keys")
        except Exception as e:
            logger.warning(f"Cache invalidation failed: {e}")

        return NewsRefreshResponse(
            status="accepted",
            message="News scrape and sentiment pipeline dispatched",
            task_id=task.id,
        )
    except Exception as e:
        logger.error(f"Failed to dispatch pipeline task: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to dispatch pipeline: {str(e)}",
        )
