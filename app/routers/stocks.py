"""
Stock price history API router.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import PriceHistoryResponse, PriceOut, StockOut
from app.models.sql_models import Price, Stock

router = APIRouter(prefix="/api/stocks", tags=["Stocks"])


@router.get("", response_model=list[StockOut])
async def list_stocks(
    nifty50_only: bool = Query(True, description="Filter to Nifty 50 only"),
    sector: str | None = Query(None, description="Filter by sector"),
    db: AsyncSession = Depends(get_db),
):
    """List all stocks, optionally filtered by Nifty 50 membership or sector."""
    query = select(Stock)

    if nifty50_only:
        query = query.where(Stock.is_nifty50 == True)  # noqa: E712
    if sector:
        query = query.where(Stock.sector == sector)

    query = query.order_by(Stock.symbol)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{symbol}/history", response_model=PriceHistoryResponse)
async def get_price_history(
    symbol: str,
    start: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(500, ge=1, le=5000, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get OHLCV price history for a stock.

    - **symbol**: NSE symbol (e.g., RELIANCE.NS)
    - **start**: Start date filter (inclusive)
    - **end**: End date filter (inclusive)
    - **limit**: Maximum number of records (default 500, max 5000)
    """
    # Look up stock
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()

    if stock is None:
        raise HTTPException(
            status_code=404,
            detail=f"Stock '{symbol}' not found. Use NSE symbol format (e.g., RELIANCE.NS).",
        )

    # Build price query
    query = select(Price).where(Price.stock_id == stock.id)

    if start:
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            query = query.where(Price.ts >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format. Use YYYY-MM-DD.")

    if end:
        try:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
            query = query.where(Price.ts <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end date format. Use YYYY-MM-DD.")

    query = query.order_by(Price.ts.desc()).limit(limit)
    result = await db.execute(query)
    prices = result.scalars().all()

    return PriceHistoryResponse(
        symbol=symbol,
        count=len(prices),
        data=[PriceOut.model_validate(p) for p in prices],
    )


@router.get("/{symbol}/risk", response_model=dict)
async def get_risk_score(
    symbol: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the latest risk score for a stock."""
    from app.models.sql_models import RiskScore

    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()

    if stock is None:
        raise HTTPException(status_code=404, detail=f"Stock '{symbol}' not found.")

    result = await db.execute(
        select(RiskScore)
        .where(RiskScore.stock_id == stock.id)
        .order_by(RiskScore.ts.desc())
        .limit(1)
    )
    risk = result.scalar_one_or_none()

    if risk is None:
        return {"symbol": symbol, "risk_score": None, "message": "No risk score computed yet."}

    return {
        "symbol": symbol,
        "ts": risk.ts.isoformat(),
        "volatility_30d": float(risk.volatility_30d) if risk.volatility_30d else None,
        "beta": float(risk.beta) if risk.beta else None,
        "sharpe_ratio": float(risk.sharpe_ratio) if risk.sharpe_ratio else None,
        "var_95": float(risk.var_95) if risk.var_95 else None,
        "composite_score": float(risk.composite_score) if risk.composite_score else None,
    }
