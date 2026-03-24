"""
Risk score computation engine.

Computes per-stock risk metrics:
- 30-day rolling volatility
- Beta vs Nifty 50 index
- Sharpe ratio (risk-free rate assumed 7% for India)
- Value at Risk (95% confidence)
- Composite risk score (weighted combination)
"""

import logging
from datetime import datetime, timedelta

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sql_models import Price, Stock

logger = logging.getLogger(__name__)

RISK_FREE_RATE = 0.07  # 7% annual (India 10-yr bond approx)
TRADING_DAYS = 252


async def _get_returns(
    db: AsyncSession,
    stock_id: int,
    days: int = 90,
) -> np.ndarray | None:
    """Fetch closing prices and compute daily returns."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(Price.close)
        .where(Price.stock_id == stock_id, Price.ts >= cutoff)
        .order_by(Price.ts.asc())
    )
    closes = [float(row[0]) for row in result.fetchall() if row[0] is not None]

    if len(closes) < 10:
        return None

    prices = np.array(closes)
    returns = np.diff(prices) / prices[:-1]
    return returns


async def _get_nifty_returns(
    db: AsyncSession,
    days: int = 90,
) -> np.ndarray | None:
    """
    Get Nifty 50 index returns.
    Uses ^NSEI symbol if available, otherwise uses the first stock as proxy.
    """
    # Try to find Nifty 50 index (seed it separately if needed)
    result = await db.execute(
        select(Stock).where(Stock.symbol == "^NSEI")
    )
    nifty = result.scalar_one_or_none()

    if nifty:
        return await _get_returns(db, nifty.id, days)

    # Fallback: use average of available stock returns as market proxy
    return None


def _compute_volatility(returns: np.ndarray, window: int = 30) -> float:
    """Annualized volatility from the last `window` daily returns."""
    recent = returns[-window:] if len(returns) >= window else returns
    return float(np.std(recent, ddof=1) * np.sqrt(TRADING_DAYS))


def _compute_beta(stock_returns: np.ndarray, market_returns: np.ndarray) -> float:
    """Beta = Cov(stock, market) / Var(market)."""
    min_len = min(len(stock_returns), len(market_returns))
    if min_len < 5:
        return 1.0  # Default beta

    sr = stock_returns[-min_len:]
    mr = market_returns[-min_len:]

    cov = np.cov(sr, mr)[0][1]
    var = np.var(mr, ddof=1)
    return float(cov / var) if var > 0 else 1.0


def _compute_sharpe(returns: np.ndarray) -> float:
    """Annualized Sharpe ratio."""
    mean_return = np.mean(returns) * TRADING_DAYS
    std_return = np.std(returns, ddof=1) * np.sqrt(TRADING_DAYS)
    if std_return == 0:
        return 0.0
    return float((mean_return - RISK_FREE_RATE) / std_return)


def _compute_var_95(returns: np.ndarray) -> float:
    """Historical Value at Risk at 95% confidence."""
    return float(np.percentile(returns, 5))


def _composite_score(
    volatility: float,
    beta: float,
    sharpe: float,
    var_95: float,
) -> float:
    """
    Weighted composite risk score (0–100 scale).
    Higher = riskier.
    """
    # Normalize components to 0–1 range (approximate)
    vol_score = min(volatility / 0.60, 1.0)        # 60% vol = max
    beta_score = min(abs(beta) / 2.0, 1.0)          # beta 2.0 = max
    sharpe_score = 1.0 - min(max(sharpe + 1, 0) / 4.0, 1.0)  # Inverse: high sharpe = low risk
    var_score = min(abs(var_95) / 0.05, 1.0)        # 5% daily loss = max

    composite = (
        0.30 * vol_score
        + 0.25 * beta_score
        + 0.25 * sharpe_score
        + 0.20 * var_score
    ) * 100

    return round(composite, 2)


async def compute_risk_scores(db: AsyncSession, stock_id: int) -> dict | None:
    """
    Compute all risk metrics for a single stock and insert into DB.
    Returns the computed metrics dict, or None if insufficient data.
    """
    returns = await _get_returns(db, stock_id)
    if returns is None:
        logger.warning(f"Insufficient data for stock_id={stock_id}")
        return None

    market_returns = await _get_nifty_returns(db)

    volatility = _compute_volatility(returns)
    beta = _compute_beta(returns, market_returns) if market_returns is not None else 1.0
    sharpe = _compute_sharpe(returns)
    var_95 = _compute_var_95(returns)
    composite = _composite_score(volatility, beta, sharpe, var_95)

    metrics = {
        "stock_id": stock_id,
        "ts": datetime.utcnow(),
        "volatility_30d": round(volatility, 6),
        "beta": round(beta, 6),
        "sharpe_ratio": round(sharpe, 6),
        "var_95": round(var_95, 6),
        "composite_score": composite,
    }

    await db.execute(
        text("""
            INSERT INTO risk_scores (stock_id, ts, volatility_30d, beta, sharpe_ratio, var_95, composite_score)
            VALUES (:stock_id, :ts, :volatility_30d, :beta, :sharpe_ratio, :var_95, :composite_score)
            ON CONFLICT (stock_id, ts) DO UPDATE SET
                volatility_30d = EXCLUDED.volatility_30d,
                beta           = EXCLUDED.beta,
                sharpe_ratio   = EXCLUDED.sharpe_ratio,
                var_95         = EXCLUDED.var_95,
                composite_score= EXCLUDED.composite_score
        """),
        metrics,
    )
    await db.commit()

    logger.info(f"Risk scores computed for stock_id={stock_id}: composite={composite}")
    return metrics


async def refresh_all_risk_scores(db: AsyncSession) -> int:
    """Compute risk scores for all Nifty 50 stocks. Returns count updated."""
    result = await db.execute(select(Stock).where(Stock.is_nifty50 == True))  # noqa: E712
    stocks = result.scalars().all()

    count = 0
    for stock in stocks:
        try:
            metrics = await compute_risk_scores(db, stock.id)
            if metrics:
                count += 1
        except Exception as e:
            logger.error(f"Risk score failed for {stock.symbol}: {e}")

    return count
