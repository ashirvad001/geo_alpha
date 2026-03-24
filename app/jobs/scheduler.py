"""
APScheduler job definitions for automated data collection.

Jobs:
1. Market data refresh — weekdays at 09:15 IST (after market open)
2. RBI bulletin check — every Monday at 10:00 IST
3. Risk score computation — weekdays at 16:30 IST (after market close)
4. GPR score refresh — 1st of every month at 08:00 IST
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")


async def job_refresh_market_data():
    """Scheduled job: Refresh all Nifty 50 stock data."""
    from app.database import async_session
    from app.services.scraper import refresh_all_nifty50

    logger.info(f"[SCHEDULER] Market data refresh started at {datetime.now()}")
    async with async_session() as db:
        try:
            count = await refresh_all_nifty50(db)
            logger.info(f"[SCHEDULER] Market data refresh complete — {count} rows upserted")
        except Exception as e:
            logger.error(f"[SCHEDULER] Market data refresh failed: {e}")


async def job_check_rbi_bulletin():
    """Scheduled job: Check for new RBI MPC bulletin."""
    from app.database import async_session
    from app.services.rbi_parser import parse_and_store_bulletin

    logger.info(f"[SCHEDULER] RBI bulletin check started at {datetime.now()}")
    async with async_session() as db:
        try:
            result = await parse_and_store_bulletin(db)
            if result:
                logger.info(f"[SCHEDULER] RBI bulletin parsed: {result}")
            else:
                logger.info("[SCHEDULER] No new RBI bulletin found")
        except Exception as e:
            logger.error(f"[SCHEDULER] RBI bulletin check failed: {e}")


async def job_compute_risk_scores():
    """Scheduled job: Recompute risk scores for all Nifty 50 stocks."""
    from app.database import async_session
    from app.services.risk_engine import refresh_all_risk_scores

    logger.info(f"[SCHEDULER] Risk score computation started at {datetime.now()}")
    async with async_session() as db:
        try:
            count = await refresh_all_risk_scores(db)
            logger.info(f"[SCHEDULER] Risk scores computed for {count} stocks")
        except Exception as e:
            logger.error(f"[SCHEDULER] Risk score computation failed: {e}")


async def job_refresh_gpr_scores():
    """Scheduled job: Refresh GPR scores for all Nifty 50 stocks (monthly)."""
    from app.database import async_session
    from app.services.gpr_engine import compute_all_gpr_scores

    logger.info(f"[SCHEDULER] GPR score refresh started at {datetime.now()}")
    async with async_session() as db:
        try:
            count = await compute_all_gpr_scores(db)
            logger.info(f"[SCHEDULER] GPR scores computed for {count} stocks")
        except Exception as e:
            logger.error(f"[SCHEDULER] GPR score refresh failed: {e}")


def configure_scheduler():
    """Register all scheduled jobs."""

    # ── Market Data: Weekdays at 09:15 IST ──────────
    scheduler.add_job(
        job_refresh_market_data,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=9,
            minute=15,
            timezone="Asia/Kolkata",
        ),
        id="market_data_refresh",
        name="Market Data Refresh (9:15 AM IST)",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hour grace period
    )

    # ── RBI Bulletin: Every Monday at 10:00 IST ─────
    scheduler.add_job(
        job_check_rbi_bulletin,
        trigger=CronTrigger(
            day_of_week="mon",
            hour=10,
            minute=0,
            timezone="Asia/Kolkata",
        ),
        id="rbi_bulletin_check",
        name="RBI Bulletin Check (Monday 10 AM IST)",
        replace_existing=True,
        misfire_grace_time=86400,  # 24 hour grace period
    )

    # ── Risk Scores: Weekdays at 16:30 IST ──────────
    scheduler.add_job(
        job_compute_risk_scores,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=16,
            minute=30,
            timezone="Asia/Kolkata",
        ),
        id="risk_score_computation",
        name="Risk Score Computation (4:30 PM IST)",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # ── GPR Scores: 1st of every month at 08:00 IST ──
    scheduler.add_job(
        job_refresh_gpr_scores,
        trigger=CronTrigger(
            day=1,
            hour=8,
            minute=0,
            timezone="Asia/Kolkata",
        ),
        id="gpr_score_refresh",
        name="GPR Score Refresh (1st of month 8 AM IST)",
        replace_existing=True,
        misfire_grace_time=86400,  # 24 hour grace period
    )

    logger.info("[SCHEDULER] All jobs configured:")
    for job in scheduler.get_jobs():
        logger.info(f"  → {job.name} | next run: {job.next_run_time}")


def start_scheduler():
    """Configure and start the APScheduler."""
    configure_scheduler()
    scheduler.start()
    logger.info("[SCHEDULER] Scheduler started")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] Scheduler stopped")
