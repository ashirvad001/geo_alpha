"""
GPR (Geopolitical Risk) API router.

Endpoints:
- GET /api/gpr/stock/{symbol} — Historical GPR scores + current score + percentile
- GET /api/gpr/heatmap — All 50 stocks sorted by GPR score + sector aggregates

Both endpoints use Redis caching with 6-hour TTL.
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, get_redis
from app.models.schemas import (
    GPRHeatmapItem,
    GPRHeatmapResponse,
    GPRScoreOut,
    GPRSectorAggregate,
    GPRStockResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gpr", tags=["Geopolitical Risk"])

CACHE_TTL = settings.gpr_cache_ttl  # 6 hours (21600 seconds)


def _serialize_datetime(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# ═══════════════════════════════════════════════════════
# GET /api/gpr/stock/{symbol}
# ═══════════════════════════════════════════════════════

@router.get("/stock/{symbol}", response_model=GPRStockResponse)
async def get_stock_gpr(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get GPR score history for a specific Nifty 50 stock.

    Returns the current GPR score, historical scores, and percentile rank.

    - **symbol**: NSE symbol (e.g., RELIANCE.NS)
    """
    # Check Redis cache
    cache_key = f"gpr:stock:{symbol}"
    try:
        redis = get_redis()
        cached = await redis.get(cache_key)
        if cached:
            logger.debug(f"Cache HIT for {cache_key}")
            data = json.loads(cached)
            return GPRStockResponse(**data)
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")

    # Cache miss — fetch from DB
    from app.services.gpr_engine import get_stock_gpr_history

    result = await get_stock_gpr_history(db, symbol)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stock '{symbol}' not found. Use NSE symbol format (e.g., RELIANCE.NS).",
        )

    stock = result["stock"]
    current = result["current"]
    history = result["history"]

    # Build response
    current_out = None
    if current:
        current_out = GPRScoreOut.model_validate(current)

    history_out = [GPRScoreOut.model_validate(h) for h in history]

    response = GPRStockResponse(
        symbol=stock.symbol,
        name=stock.name,
        sector=stock.sector,
        gpr_sector=current.gpr_sector if current else None,
        current_score=current_out,
        history=history_out,
        history_count=len(history_out),
    )

    # Cache the response
    try:
        redis = get_redis()
        await redis.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(response.model_dump(), default=_serialize_datetime),
        )
        logger.debug(f"Cached {cache_key} with TTL={CACHE_TTL}s")
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")

    return response


# ═══════════════════════════════════════════════════════
# GET /api/gpr/heatmap
# ═══════════════════════════════════════════════════════

@router.get("/heatmap", response_model=GPRHeatmapResponse)
async def get_gpr_heatmap(
    db: AsyncSession = Depends(get_db),
):
    """
    Get GPR heatmap for all Nifty 50 stocks.

    Returns all 50 stocks sorted by GPR score (descending) with sector aggregates.
    """
    # Check Redis cache
    cache_key = "gpr:heatmap"
    try:
        redis = get_redis()
        cached = await redis.get(cache_key)
        if cached:
            logger.debug(f"Cache HIT for {cache_key}")
            data = json.loads(cached)
            return GPRHeatmapResponse(**data)
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")

    # Cache miss — fetch from DB
    from app.services.gpr_engine import get_gpr_heatmap as _get_heatmap

    heatmap_data = await _get_heatmap(db)

    response = GPRHeatmapResponse(
        stocks=[GPRHeatmapItem(**s) for s in heatmap_data["stocks"]],
        sectors=[GPRSectorAggregate(**s) for s in heatmap_data["sectors"]],
        total_stocks=len(heatmap_data["stocks"]),
        last_updated=heatmap_data["last_updated"],
    )

    # Cache the response
    try:
        redis = get_redis()
        await redis.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(response.model_dump(), default=_serialize_datetime),
        )
        logger.debug(f"Cached {cache_key} with TTL={CACHE_TTL}s")
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")

    return response


# ═══════════════════════════════════════════════════════
# POST /api/gpr/refresh (admin trigger)
# ═══════════════════════════════════════════════════════

@router.post("/refresh")
async def refresh_gpr_scores(
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger GPR score refresh for all Nifty 50 stocks.

    Fetches latest GPR data from FRED (or synthetic), computes scores,
    stores in DB, and invalidates Redis cache.
    """
    from app.services.gpr_engine import compute_all_gpr_scores

    try:
        count = await compute_all_gpr_scores(db)
        return {
            "status": "success",
            "message": f"GPR scores refreshed for {count} stocks",
            "stocks_scored": count,
        }
    except Exception as e:
        logger.error(f"GPR refresh failed: {e}")
        raise HTTPException(status_code=500, detail=f"GPR refresh failed: {str(e)}")
