"""
Geopolitical Risk (GPR) Scoring Engine for Nifty 50 Stocks.

Computes per-stock GPR scores based on:
1. Sector baseline multipliers (global supply chain exposure)
2. Normalized GPR index (weighted blend of global + India)
3. International revenue exposure factor

Formula:
    gpr_score = sector_baseline × composite_gpr_norm × revenue_exposure_factor

Where:
    composite_gpr_norm = 0.7 × global_norm + 0.3 × india_norm
    revenue_exposure_factor = 0.5 + (intl_revenue_pct / 100)
"""

import logging
from collections import defaultdict
from datetime import datetime

import numpy as np
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_redis
from app.models.sql_models import GPRScore, Stock

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
# Sector Classification & Baseline Multipliers
# ═══════════════════════════════════════════════════════

# Maps the existing stocks.sector values → GPR sector label
SECTOR_MAPPING: dict[str, str] = {
    "Energy": "Energy",
    "Information Technology": "IT",
    "Financial Services": "Banking",
    "FMCG": "FMCG",
    "Automobile": "Auto",
    "Healthcare": "Pharma",
    "Metals & Mining": "Metals",
    "Construction": "Infra",
    "Construction Materials": "Infra",
    "Infrastructure": "Infra",
    "Power": "Infra",
    # Unmapped sectors → neutral
    "Telecommunication": "Telecom",
    "Consumer Durables": "Consumer",
    "Consumer Services": "Consumer",
    "Diversified": "Diversified",
}

# Sector baseline GPR multipliers (higher = more exposed to geopolitical risk)
SECTOR_BASELINES: dict[str, float] = {
    "Energy": 1.8,      # Highest: oil price shocks, OPEC, sanctions
    "IT": 1.6,          # Offshoring regulations, visa policies, trade wars
    "Metals": 1.5,      # Commodity supply chains, tariffs, China exposure
    "Infra": 1.4,       # Construction materials, cross-border projects
    "Auto": 1.3,        # Global supply chains, chip shortages, trade barriers
    "Banking": 1.2,     # FII flows, currency risk, cross-border regulations
    "Pharma": 1.1,      # API sourcing from China, FDA approvals, patent wars
    "Telecom": 1.0,     # Mostly domestic, neutral
    "Consumer": 1.0,    # Mostly domestic, neutral
    "Diversified": 1.0, # Mixed exposure, neutral
    "FMCG": 0.7,        # Predominantly domestic, low GPR sensitivity
}

DEFAULT_BASELINE = 1.0


# ═══════════════════════════════════════════════════════
# International Revenue Exposure (% from NSE annual reports)
# ═══════════════════════════════════════════════════════

# Approximate international revenue % for each Nifty 50 stock
# Sources: Annual reports, investor presentations (FY2024-25 estimates)
REVENUE_EXPOSURE: dict[str, float] = {
    # Energy
    "RELIANCE.NS": 35.0,
    "ONGC.NS": 5.0,
    "BPCL.NS": 8.0,

    # Information Technology (high international exposure)
    "TCS.NS": 95.0,
    "INFY.NS": 97.0,
    "HCLTECH.NS": 93.0,
    "WIPRO.NS": 93.0,
    "TECHM.NS": 90.0,

    # Financial Services (mostly domestic)
    "HDFCBANK.NS": 5.0,
    "ICICIBANK.NS": 8.0,
    "SBIN.NS": 3.0,
    "KOTAKBANK.NS": 2.0,
    "AXISBANK.NS": 5.0,
    "BAJFINANCE.NS": 1.0,
    "BAJAJFINSV.NS": 2.0,
    "HDFCLIFE.NS": 1.0,
    "SBILIFE.NS": 1.0,
    "INDUSINDBK.NS": 4.0,

    # FMCG
    "HINDUNILVR.NS": 12.0,
    "ITC.NS": 15.0,
    "BRITANNIA.NS": 8.0,
    "NESTLEIND.NS": 5.0,
    "TATACONSUM.NS": 20.0,

    # Automobile
    "MARUTI.NS": 15.0,
    "TATAMOTORS.NS": 65.0,  # JLR is majority revenue
    "M&M.NS": 25.0,
    "EICHERMOT.NS": 20.0,
    "HEROMOTOCO.NS": 12.0,
    "BAJAJ-AUTO.NS": 40.0,

    # Healthcare / Pharma (significant exports)
    "SUNPHARMA.NS": 70.0,
    "DIVISLAB.NS": 80.0,
    "CIPLA.NS": 55.0,
    "DRREDDY.NS": 75.0,
    "APOLLOHOSP.NS": 8.0,

    # Metals & Mining
    "JSWSTEEL.NS": 25.0,
    "TATASTEEL.NS": 45.0,  # Tata Steel Europe
    "HINDALCO.NS": 60.0,   # Novelis
    "COALINDIA.NS": 2.0,

    # Infrastructure / Construction / Power
    "LT.NS": 30.0,
    "ULTRACEMCO.NS": 10.0,
    "ADANIENT.NS": 15.0,
    "ADANIPORTS.NS": 20.0,
    "NTPC.NS": 2.0,
    "POWERGRID.NS": 1.0,
    "GRASIM.NS": 12.0,

    # Telecom
    "BHARTIARTL.NS": 30.0,  # Africa operations

    # Consumer
    "ASIANPAINT.NS": 18.0,
    "TITAN.NS": 5.0,
    "DMART.NS": 0.0,
}

DEFAULT_REVENUE_EXPOSURE = 10.0  # fallback


def get_gpr_sector(db_sector: str | None) -> str:
    """Map the database sector value to a GPR sector label."""
    if not db_sector:
        return "Diversified"
    return SECTOR_MAPPING.get(db_sector, "Diversified")


def get_sector_baseline(gpr_sector: str) -> float:
    """Get sector baseline GPR multiplier."""
    return SECTOR_BASELINES.get(gpr_sector, DEFAULT_BASELINE)


def get_revenue_exposure(symbol: str) -> float:
    """Get international revenue exposure % for a stock."""
    return REVENUE_EXPOSURE.get(symbol, DEFAULT_REVENUE_EXPOSURE)


def compute_revenue_factor(intl_revenue_pct: float) -> float:
    """
    Convert international revenue % to exposure factor.
    0% → 0.5 (floor: purely domestic still has some exposure)
    100% → 1.5 (ceiling)
    """
    return round(0.5 + (intl_revenue_pct / 100.0), 4)


def compute_gpr_score(
    sector_baseline: float,
    gpr_global_norm: float,
    gpr_india_norm: float,
    revenue_exposure_pct: float,
) -> float:
    """
    Compute the final GPR score for a stock.

    gpr_score = sector_baseline × composite_gpr_norm × revenue_exposure_factor

    Where composite_gpr_norm = 0.7 × global + 0.3 × india
    """
    composite_norm = 0.7 * gpr_global_norm + 0.3 * gpr_india_norm
    revenue_factor = compute_revenue_factor(revenue_exposure_pct)
    return round(sector_baseline * composite_norm * revenue_factor, 4)


# ═══════════════════════════════════════════════════════
# Main Engine Functions
# ═══════════════════════════════════════════════════════

async def compute_all_gpr_scores(db: AsyncSession) -> int:
    """
    Compute GPR scores for all Nifty 50 stocks using the latest
    GPR index values. Upserts into gpr_scores table.

    Returns the number of stocks scored.
    """
    from app.services.fred_client import fetch_and_store_gpr

    # Step 1: Refresh GPR data from FRED
    gpr_data = await fetch_and_store_gpr(db)
    gpr_global_norm = gpr_data["gpr_global_norm"]
    gpr_india_norm = gpr_data["gpr_india_norm"]

    logger.info(
        f"GPR norms — global: {gpr_global_norm:.4f}, india: {gpr_india_norm:.4f}"
    )

    # Step 2: Get all Nifty 50 stocks
    result = await db.execute(
        select(Stock).where(Stock.is_nifty50 == True)  # noqa: E712
    )
    stocks = result.scalars().all()

    # Step 3: Compute scores for each stock
    now = datetime.utcnow()
    scores: list[dict] = []

    for stock in stocks:
        gpr_sector = get_gpr_sector(stock.sector)
        baseline = get_sector_baseline(gpr_sector)
        rev_pct = get_revenue_exposure(stock.symbol)
        rev_factor = compute_revenue_factor(rev_pct)
        score = compute_gpr_score(baseline, gpr_global_norm, gpr_india_norm, rev_pct)

        scores.append({
            "stock_id": stock.id,
            "symbol": stock.symbol,
            "ts": now,
            "gpr_sector": gpr_sector,
            "sector_baseline": baseline,
            "gpr_global_norm": round(0.7 * gpr_global_norm + 0.3 * gpr_india_norm, 6),
            "revenue_exposure_pct": rev_pct,
            "revenue_exposure_fac": rev_factor,
            "gpr_score": score,
        })

    # Step 4: Compute percentile ranks
    all_scores = [s["gpr_score"] for s in scores]
    if all_scores:
        score_array = np.array(all_scores)
        for s in scores:
            pct = float(np.sum(score_array <= s["gpr_score"]) / len(score_array) * 100)
            s["percentile_rank"] = round(pct, 2)

    # Step 5: Upsert into gpr_scores
    count = 0
    for s in scores:
        try:
            await db.execute(
                text("""
                    INSERT INTO gpr_scores
                        (stock_id, ts, gpr_sector, sector_baseline, gpr_global_norm,
                         revenue_exposure_pct, revenue_exposure_fac, gpr_score, percentile_rank)
                    VALUES
                        (:stock_id, :ts, :gpr_sector, :sector_baseline, :gpr_global_norm,
                         :revenue_exposure_pct, :revenue_exposure_fac, :gpr_score, :percentile_rank)
                    ON CONFLICT (stock_id, ts) DO UPDATE SET
                        gpr_sector         = EXCLUDED.gpr_sector,
                        sector_baseline    = EXCLUDED.sector_baseline,
                        gpr_global_norm    = EXCLUDED.gpr_global_norm,
                        revenue_exposure_pct = EXCLUDED.revenue_exposure_pct,
                        revenue_exposure_fac = EXCLUDED.revenue_exposure_fac,
                        gpr_score          = EXCLUDED.gpr_score,
                        percentile_rank    = EXCLUDED.percentile_rank
                """),
                s,
            )
            count += 1
        except Exception as e:
            logger.error(f"GPR score upsert failed for {s.get('symbol')}: {e}")

    await db.commit()
    logger.info(f"GPR scores computed for {count} stocks")

    # Step 6: Invalidate Redis cache
    await _invalidate_gpr_cache()

    return count


async def _invalidate_gpr_cache() -> None:
    """Delete all GPR-related cache keys."""
    try:
        redis = get_redis()
        cursor = "0"
        deleted = 0
        while cursor:
            cursor, keys = await redis.scan(cursor=cursor, match="gpr:*", count=100)
            if keys:
                await redis.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break
        logger.info(f"Invalidated {deleted} GPR cache keys")
    except Exception as e:
        logger.warning(f"Redis cache invalidation failed: {e}")


async def get_stock_gpr_history(
    db: AsyncSession,
    symbol: str,
) -> dict | None:
    """
    Get GPR score history for a specific stock.

    Returns:
        {
            "stock": Stock object,
            "current": latest GPRScore or None,
            "history": list of GPRScore objects,
        }
        or None if stock not found.
    """
    result = await db.execute(select(Stock).where(Stock.symbol == symbol))
    stock = result.scalar_one_or_none()
    if stock is None:
        return None

    # Get all GPR scores for this stock
    result = await db.execute(
        select(GPRScore)
        .where(GPRScore.stock_id == stock.id)
        .order_by(GPRScore.ts.desc())
    )
    all_scores = result.scalars().all()

    current = all_scores[0] if all_scores else None

    return {
        "stock": stock,
        "current": current,
        "history": all_scores,
    }


async def get_gpr_heatmap(db: AsyncSession) -> dict:
    """
    Get GPR heatmap data: all 50 stocks sorted by GPR score descending,
    with sector-level aggregates.

    Returns:
        {
            "stocks": list of dicts with stock GPR data,
            "sectors": list of sector aggregate dicts,
            "last_updated": datetime or None,
        }
    """
    # Get the latest GPR score for each stock using a subquery
    latest_ts_subq = (
        select(
            GPRScore.stock_id,
            func.max(GPRScore.ts).label("max_ts"),
        )
        .group_by(GPRScore.stock_id)
        .subquery()
    )

    result = await db.execute(
        select(GPRScore, Stock)
        .join(Stock, GPRScore.stock_id == Stock.id)
        .join(
            latest_ts_subq,
            (GPRScore.stock_id == latest_ts_subq.c.stock_id)
            & (GPRScore.ts == latest_ts_subq.c.max_ts),
        )
        .where(Stock.is_nifty50 == True)  # noqa: E712
        .order_by(GPRScore.gpr_score.desc())
    )
    rows = result.all()

    stocks = []
    sector_data: dict[str, list[float]] = defaultdict(list)
    last_updated = None

    for gpr_score, stock in rows:
        score_val = float(gpr_score.gpr_score) if gpr_score.gpr_score else 0.0
        gpr_sector = gpr_score.gpr_sector or "Unknown"

        stocks.append({
            "symbol": stock.symbol,
            "name": stock.name,
            "sector": stock.sector,
            "gpr_sector": gpr_sector,
            "gpr_score": score_val,
            "percentile_rank": float(gpr_score.percentile_rank) if gpr_score.percentile_rank else 0.0,
            "sector_baseline": float(gpr_score.sector_baseline) if gpr_score.sector_baseline else 1.0,
            "revenue_exposure_pct": float(gpr_score.revenue_exposure_pct) if gpr_score.revenue_exposure_pct else 0.0,
        })

        sector_data[gpr_sector].append(score_val)

        if last_updated is None or gpr_score.ts > last_updated:
            last_updated = gpr_score.ts

    # Compute sector aggregates
    sectors = []
    for sector_name, score_list in sorted(sector_data.items(), key=lambda x: -np.mean(x[1])):
        sectors.append({
            "gpr_sector": sector_name,
            "avg_gpr_score": round(float(np.mean(score_list)), 4),
            "max_gpr_score": round(float(np.max(score_list)), 4),
            "min_gpr_score": round(float(np.min(score_list)), 4),
            "stock_count": len(score_list),
            "baseline": get_sector_baseline(sector_name),
        })

    return {
        "stocks": stocks,
        "sectors": sectors,
        "last_updated": last_updated,
    }
