"""
RBI indicators API router.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import RBIIndicatorOut, RBILatestResponse
from app.models.sql_models import RBIIndicator

router = APIRouter(prefix="/api/rbi", tags=["RBI Indicators"])


@router.get("/latest", response_model=RBILatestResponse)
async def get_latest_rbi(
    db: AsyncSession = Depends(get_db),
):
    """
    Get the most recent RBI macroeconomic indicators.

    Returns the latest record from the rbi_indicators table
    (repo rate, CPI, GDP growth, forex reserves, etc.)
    """
    # Get latest record
    result = await db.execute(
        select(RBIIndicator).order_by(RBIIndicator.ts.desc()).limit(1)
    )
    latest = result.scalar_one_or_none()

    # Get total count
    count_result = await db.execute(select(func.count(RBIIndicator.id)))
    total = count_result.scalar() or 0

    return RBILatestResponse(
        latest=RBIIndicatorOut.model_validate(latest) if latest else None,
        history_count=total,
    )


@router.get("/history", response_model=list[RBIIndicatorOut])
async def get_rbi_history(
    limit: int = Query(20, ge=1, le=200, description="Max records to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical RBI indicators, ordered by most recent first.
    """
    result = await db.execute(
        select(RBIIndicator).order_by(RBIIndicator.ts.desc()).limit(limit)
    )
    records = result.scalars().all()
    return [RBIIndicatorOut.model_validate(r) for r in records]
