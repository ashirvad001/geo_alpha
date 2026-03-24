"""
Data refresh API router.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import RefreshRequest, RefreshResponse
from app.models.sql_models import Stock
from app.services.rbi_parser import parse_and_store_bulletin
from app.services.scraper import fetch_stock_history, refresh_all_nifty50

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/data", tags=["Data Management"])


async def _run_refresh(
    symbols: list[str] | None,
    include_rbi: bool,
):
    """
    Background task: refresh stock data and optionally RBI indicators.
    Uses its own DB session since this runs outside the request lifecycle.
    """
    from app.database import async_session

    async with async_session() as db:
        try:
            if symbols:
                for symbol in symbols:
                    try:
                        await fetch_stock_history(symbol, db)
                    except Exception as e:
                        logger.error(f"Refresh failed for {symbol}: {e}")
            else:
                await refresh_all_nifty50(db)

            if include_rbi:
                await parse_and_store_bulletin(db)

            logger.info("Data refresh completed successfully")
        except Exception as e:
            logger.error(f"Data refresh failed: {e}")


@router.post("/refresh", response_model=RefreshResponse)
async def trigger_refresh(
    request: RefreshRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a data refresh.

    - If `symbols` is provided, only those stocks are refreshed.
    - If `symbols` is None, all Nifty 50 stocks are refreshed.
    - If `include_rbi` is True, RBI indicators are also refreshed.

    The refresh runs as a **background task** — this endpoint returns immediately.
    """
    # Validate symbols if provided
    if request.symbols:
        for symbol in request.symbols:
            result = await db.execute(select(Stock).where(Stock.symbol == symbol))
            if result.scalar_one_or_none() is None:
                return RefreshResponse(
                    status="error",
                    message=f"Unknown symbol: {symbol}. Use format like RELIANCE.NS",
                    stocks_updated=0,
                    rbi_updated=False,
                )

    # Schedule background refresh
    background_tasks.add_task(_run_refresh, request.symbols, request.include_rbi)

    target = ", ".join(request.symbols) if request.symbols else "all Nifty 50"
    return RefreshResponse(
        status="accepted",
        message=f"Refresh job started for {target}. RBI: {'yes' if request.include_rbi else 'no'}.",
        stocks_updated=0,
        rbi_updated=False,
    )
