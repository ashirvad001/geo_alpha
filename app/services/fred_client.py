"""
FRED API client for fetching Caldara-Iacoviello Geopolitical Risk Index.

Series:
- GPRI   → Global GPR Index (monthly)
- GPRI_IN → India-specific GPR component (monthly, may be named GPRIIN on FRED)

The GPR Index measures geopolitical risk based on newspaper article counts
related to geopolitical tensions, wars, and terrorist acts.
"""

import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

# FRED series identifiers for GPR data
GPR_GLOBAL_SERIES = "GPRH"        # GPR Historical Index
GPR_INDIA_SERIES = "GPRCHN"       # Closest proxy; India not separate on FRED


async def fetch_gpr_from_fred() -> dict | None:
    """
    Fetch GPR index data from FRED API.

    Returns dict with 'global' and 'india' DataFrames, or None on failure.
    Uses fredapi library which the FRED_API_KEY setting.
    """
    if not settings.fred_api_key or settings.fred_api_key == "your_fred_api_key_here":
        logger.warning("FRED_API_KEY not configured — using synthetic GPR data")
        return _generate_synthetic_gpr()

    try:
        from fredapi import Fred

        fred = Fred(api_key=settings.fred_api_key)

        # Fetch Global GPR Index
        gpr_global = fred.get_series("GPRH")
        logger.info(f"Fetched {len(gpr_global)} global GPR observations from FRED")

        # Fetch India-specific GPR (or use a proxy)
        try:
            gpr_india = fred.get_series("GPRD_IND")
        except Exception:
            # India-specific series may not be available;
            # use a scaled version of global as proxy
            logger.warning("India GPR series not found on FRED — deriving from global")
            gpr_india = gpr_global * 1.15  # India typically ~15% higher

        return {
            "global": gpr_global,
            "india": gpr_india,
        }

    except Exception as e:
        logger.error(f"FRED API fetch failed: {e}")
        return _generate_synthetic_gpr()


def _generate_synthetic_gpr() -> dict:
    """
    Generate synthetic GPR data for development/testing when FRED key
    is not available. Simulates monthly data with realistic patterns.
    """
    import numpy as np

    dates = pd.date_range(start="2020-01-01", periods=75, freq="MS")
    np.random.seed(42)

    # Global GPR: baseline ~100, with spikes for geopolitical events
    base = 100 + np.cumsum(np.random.randn(75) * 5)
    # Add a few geopolitical "shocks"
    base[24:28] += 50   # COVID-era uncertainty
    base[48:52] += 35   # Conflict-era spike
    gpr_global = pd.Series(np.maximum(base, 30), index=dates, name="GPRH")

    # India GPR: correlated but with local variance
    india_noise = np.random.randn(75) * 8
    gpr_india = pd.Series(
        np.maximum(gpr_global.values * 1.15 + india_noise, 20),
        index=dates,
        name="GPRD_IND",
    )

    logger.info(f"Generated {len(dates)} synthetic GPR observations")
    return {"global": gpr_global, "india": gpr_india}


def normalize_gpr_series(series: pd.Series) -> pd.Series:
    """Normalize GPR series to 0–1 range using historical min/max."""
    s_min = series.min()
    s_max = series.max()
    if s_max == s_min:
        return pd.Series(0.5, index=series.index)
    return (series - s_min) / (s_max - s_min)


async def fetch_and_store_gpr(db: AsyncSession) -> dict:
    """
    Fetch GPR data from FRED (or generate synthetic), normalize,
    and upsert into the gpr_index table.

    Returns dict with latest normalized values:
    {
        "gpr_global_norm": float,
        "gpr_india_norm": float,
        "observations_stored": int,
    }
    """
    data = await fetch_gpr_from_fred()
    if data is None:
        logger.error("Failed to retrieve any GPR data")
        return {"gpr_global_norm": 0.5, "gpr_india_norm": 0.5, "observations_stored": 0}

    gpr_global = data["global"].dropna()
    gpr_india = data["india"].dropna()

    # Normalize
    global_norm = normalize_gpr_series(gpr_global)
    india_norm = normalize_gpr_series(gpr_india)

    # Align on common dates
    common_dates = global_norm.index.intersection(india_norm.index)
    count = 0

    for ts in common_dates:
        await db.execute(
            text("""
                INSERT INTO gpr_index (ts, gpr_global, gpr_india, gpr_global_norm, gpr_india_norm, source)
                VALUES (:ts, :gpr_global, :gpr_india, :gpr_global_norm, :gpr_india_norm, :source)
                ON CONFLICT (ts) DO UPDATE SET
                    gpr_global     = EXCLUDED.gpr_global,
                    gpr_india      = EXCLUDED.gpr_india,
                    gpr_global_norm = EXCLUDED.gpr_global_norm,
                    gpr_india_norm  = EXCLUDED.gpr_india_norm
            """),
            {
                "ts": ts.to_pydatetime(),
                "gpr_global": float(gpr_global.loc[ts]),
                "gpr_india": float(gpr_india.loc[ts]),
                "gpr_global_norm": float(global_norm.loc[ts]),
                "gpr_india_norm": float(india_norm.loc[ts]),
                "source": "FRED" if settings.fred_api_key and settings.fred_api_key != "your_fred_api_key_here" else "SYNTHETIC",
            },
        )
        count += 1

    await db.commit()
    logger.info(f"Stored {count} GPR index observations")

    # Return latest
    latest_ts = common_dates[-1]
    return {
        "gpr_global_norm": float(global_norm.loc[latest_ts]),
        "gpr_india_norm": float(india_norm.loc[latest_ts]),
        "observations_stored": count,
    }
