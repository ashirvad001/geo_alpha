"""
Temporal-decay sentiment aggregation.

Implements:
    sentiment_score = Σ(score_i × exp(-λ × Δt_i))
where λ = 0.2 (configurable) and Δt is in days.

Computes 7-day rolling sentiment per stock and trend analysis.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone

from app.config import settings

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# Core Decay Math
# ═══════════════════════════════════════════════════════

LAMBDA = settings.sentiment_decay_lambda   # 0.2
WINDOW_DAYS = settings.sentiment_window_days  # 7


def compute_decayed_sentiment(
    scores: list[dict],
    reference_time: datetime | None = None,
    decay_lambda: float = LAMBDA,
) -> float:
    """
    Compute exponentially time-decayed sentiment score.

    Formula: Σ(score_i × exp(-λ × Δt_i))

    Args:
        scores: list of dicts with keys:
            - "composite_score": float in [-1, +1]
            - "published_at": datetime
        reference_time: the "now" reference (defaults to UTC now)
        decay_lambda: decay rate (default 0.2)

    Returns:
        Decayed aggregate sentiment score (float)
    """
    if not scores:
        return 0.0

    if reference_time is None:
        reference_time = datetime.now(timezone.utc)

    # Ensure reference_time is timezone-aware
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    total = 0.0
    weight_sum = 0.0

    for entry in scores:
        score = entry.get("composite_score", 0.0)
        pub_time = entry.get("published_at")

        if pub_time is None:
            continue

        # Ensure pub_time is timezone-aware
        if pub_time.tzinfo is None:
            pub_time = pub_time.replace(tzinfo=timezone.utc)

        delta_days = (reference_time - pub_time).total_seconds() / 86400.0
        if delta_days < 0:
            delta_days = 0.0  # Future articles get full weight

        weight = math.exp(-decay_lambda * delta_days)
        total += score * weight
        weight_sum += weight

    # Normalise by total weight to keep score in [-1, +1]
    if weight_sum > 0:
        return total / weight_sum
    return 0.0


# ═══════════════════════════════════════════════════════
# Rolling Sentiment Computation
# ═══════════════════════════════════════════════════════

async def compute_rolling_sentiment(
    symbol: str,
    window_days: int = WINDOW_DAYS,
) -> dict:
    """
    Compute 7-day rolling sentiment for a specific stock symbol.

    Queries MongoDB for articles mentioning this symbol within the window,
    computes decayed aggregate, and determines trend.

    Returns:
        {
            "composite_score": float,
            "positive_pct": float,
            "negative_pct": float,
            "neutral_pct": float,
            "article_count": int,
            "trend": "bullish" | "bearish" | "neutral",
            "window_days": int,
            "last_updated": datetime,
        }
    """
    from app.database import get_mongo_db

    db = get_mongo_db()
    collection = db["raw_news_articles"]

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=window_days)
    prev_window_start = window_start - timedelta(days=window_days)

    # ── Current window articles ───────────────────────
    current_articles = await collection.find({
        "stock_mentions": symbol,
        "processed": True,
        "sentiment": {"$ne": None},
        "scraped_at": {"$gte": window_start},
    }).to_list(length=500)

    # ── Previous window articles (for trend) ──────────
    prev_articles = await collection.find({
        "stock_mentions": symbol,
        "processed": True,
        "sentiment": {"$ne": None},
        "scraped_at": {"$gte": prev_window_start, "$lt": window_start},
    }).to_list(length=500)

    # ── Build scores list for decay computation ───────
    current_scores = []
    pos_count = neg_count = neu_count = 0

    for art in current_articles:
        sent = art.get("sentiment", {})
        composite = sent.get("composite_score", 0.0)
        label = sent.get("label", "neutral")

        current_scores.append({
            "composite_score": composite,
            "published_at": art.get("publish_time") or art.get("scraped_at"),
        })

        if label == "positive":
            pos_count += 1
        elif label == "negative":
            neg_count += 1
        else:
            neu_count += 1

    prev_scores = []
    for art in prev_articles:
        sent = art.get("sentiment", {})
        composite = sent.get("composite_score", 0.0)
        prev_scores.append({
            "composite_score": composite,
            "published_at": art.get("publish_time") or art.get("scraped_at"),
        })

    # ── Compute decayed scores ────────────────────────
    current_decayed = compute_decayed_sentiment(current_scores, reference_time=now)
    prev_decayed = compute_decayed_sentiment(
        prev_scores,
        reference_time=window_start,  # Reference from current window start
    )

    # ── Trend determination ───────────────────────────
    diff = current_decayed - prev_decayed
    if diff > 0.05:
        trend = "bullish"
    elif diff < -0.05:
        trend = "bearish"
    else:
        trend = "neutral"

    # ── Percentage breakdown ──────────────────────────
    total = pos_count + neg_count + neu_count
    if total > 0:
        positive_pct = round(pos_count / total * 100, 1)
        negative_pct = round(neg_count / total * 100, 1)
        neutral_pct = round(neu_count / total * 100, 1)
    else:
        positive_pct = negative_pct = neutral_pct = 0.0

    return {
        "composite_score": round(current_decayed, 4),
        "positive_pct": positive_pct,
        "negative_pct": negative_pct,
        "neutral_pct": neutral_pct,
        "article_count": total,
        "trend": trend,
        "window_days": window_days,
        "last_updated": now,
    }


async def compute_all_sentiments() -> dict[str, dict]:
    """
    Compute rolling sentiment for all Nifty 50 stocks that
    have at least one mention in the current window.

    Returns:
        dict mapping symbol → sentiment result
    """
    from app.nlp.ticker_map import get_all_symbols

    results: dict[str, dict] = {}
    for symbol in get_all_symbols():
        try:
            result = await compute_rolling_sentiment(symbol)
            if result["article_count"] > 0:
                results[symbol] = result
        except Exception as e:
            logger.error(f"Sentiment computation failed for {symbol}: {e}")

    logger.info(f"Computed sentiment for {len(results)} stocks")
    return results
