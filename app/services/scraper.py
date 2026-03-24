"""
NSE / yfinance stock data scraper.

Features:
- Rate limiting via asyncio.Semaphore
- Retry logic via tenacity
- Bulk upsert into PostgreSQL prices table
"""

import asyncio
import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.models.sql_models import Price, Stock

logger = logging.getLogger(__name__)

# Global rate-limiter semaphore
_semaphore: asyncio.Semaphore | None = None


def _get_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(settings.nse_rate_limit)
    return _semaphore


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, Exception)),
    before_sleep=lambda retry_state: logger.warning(
        f"Retry {retry_state.attempt_number} for stock download..."
    ),
)
def _download_stock_data(
    symbol: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    """
    Download OHLCV data from yfinance with retry logic.
    Runs in a thread pool (called via asyncio.to_thread).
    """
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end, auto_adjust=False)

    if df.empty:
        logger.warning(f"No data returned for {symbol} ({start} → {end})")
        return df

    df = df.reset_index()
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]
    return df


async def fetch_stock_history(
    symbol: str,
    db: AsyncSession,
    start: str | None = None,
    end: str | None = None,
) -> int:
    """
    Fetch OHLCV history for a single stock and upsert into the DB.

    Args:
        symbol: yfinance-compatible symbol (e.g. 'RELIANCE.NS')
        db: async SQLAlchemy session
        start: start date string (YYYY-MM-DD), defaults to 1 year ago
        end: end date string (YYYY-MM-DD), defaults to today

    Returns:
        Number of rows upserted.
    """
    sem = _get_semaphore()

    if not start:
        start = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not end:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    # Look up stock_id
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    if stock is None:
        logger.error(f"Stock {symbol} not found in database")
        return 0

    # Rate-limited download
    async with sem:
        logger.info(f"Downloading {symbol} data ({start} → {end})")
        df = await asyncio.to_thread(_download_stock_data, symbol, start, end)

    if df.empty:
        return 0

    # Bulk upsert via raw SQL for performance
    rows_upserted = 0
    for _, row in df.iterrows():
        ts = row.get("date", row.get("datetime"))
        if ts is None:
            continue

        # Ensure timezone-aware timestamp
        if hasattr(ts, "tz") and ts.tz is None:
            ts = ts.tz_localize("UTC")

        await db.execute(
            text("""
                INSERT INTO prices (stock_id, ts, open, high, low, close, adj_close, volume)
                VALUES (:stock_id, :ts, :open, :high, :low, :close, :adj_close, :volume)
                ON CONFLICT (stock_id, ts)
                DO UPDATE SET
                    open      = EXCLUDED.open,
                    high      = EXCLUDED.high,
                    low       = EXCLUDED.low,
                    close     = EXCLUDED.close,
                    adj_close = EXCLUDED.adj_close,
                    volume    = EXCLUDED.volume
            """),
            {
                "stock_id": stock.id,
                "ts": str(ts),
                "open": float(row.get("open", 0)) if pd.notna(row.get("open")) else None,
                "high": float(row.get("high", 0)) if pd.notna(row.get("high")) else None,
                "low": float(row.get("low", 0)) if pd.notna(row.get("low")) else None,
                "close": float(row.get("close", 0)) if pd.notna(row.get("close")) else None,
                "adj_close": float(row.get("adj_close", row.get("adj close", 0)))
                if pd.notna(row.get("adj_close", row.get("adj close")))
                else None,
                "volume": int(row.get("volume", 0)) if pd.notna(row.get("volume")) else None,
            },
        )
        rows_upserted += 1

    await db.commit()
    logger.info(f"Upserted {rows_upserted} rows for {symbol}")
    return rows_upserted


async def refresh_all_nifty50(db: AsyncSession) -> int:
    """
    Refresh price data for all Nifty 50 stocks.
    Returns total rows upserted.
    """
    result = await db.execute(select(Stock).where(Stock.is_nifty50 == True))  # noqa: E712
    stocks = result.scalars().all()

    total = 0
    for stock in stocks:
        try:
            count = await fetch_stock_history(stock.symbol, db)
            total += count
        except Exception as e:
            logger.error(f"Failed to refresh {stock.symbol}: {e}")
            continue

    return total
