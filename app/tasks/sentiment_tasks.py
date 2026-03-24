"""
Celery tasks for the news sentiment pipeline.

Tasks:
- task_scrape_news: scrape all sources, store in MongoDB
- task_process_sentiment: run NER + FinBERT on unprocessed articles
- task_full_pipeline: chain scrape → process
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from app.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine from synchronous Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop (shouldn't happen in worker)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery_app.task(name="app.tasks.sentiment_tasks.task_scrape_news", bind=True)
def task_scrape_news(self) -> dict:
    """
    Scrape news from all sources and store in MongoDB.

    Returns:
        {"status": "success", "articles_scraped": int, "articles_stored": int}
    """
    logger.info("Starting news scrape task...")

    async def _scrape():
        from app.services.news_scrapers import scrape_all_sources, store_articles_mongo

        articles = await scrape_all_sources()
        stored = await store_articles_mongo(articles)
        return len(articles), stored

    try:
        scraped, stored = _run_async(_scrape())
        result = {
            "status": "success",
            "articles_scraped": scraped,
            "articles_stored": stored,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"Scrape task complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Scrape task failed: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(name="app.tasks.sentiment_tasks.task_process_sentiment", bind=True)
def task_process_sentiment(self) -> dict:
    """
    Process unprocessed articles: extract stock mentions + FinBERT scoring.

    Batch-processes articles in groups of 32 for GPU efficiency.

    Returns:
        {"status": "success", "articles_processed": int}
    """
    logger.info("Starting sentiment processing task...")

    async def _process():
        from app.database import get_mongo_db
        from app.nlp.finbert_scorer import get_scorer
        from app.nlp.ner_extractor import extract_stock_mentions

        db = get_mongo_db()
        collection = db["raw_news_articles"]

        # Fetch unprocessed articles
        cursor = collection.find({"processed": False}).limit(500)
        articles = await cursor.to_list(length=500)

        if not articles:
            logger.info("No unprocessed articles found")
            return 0

        logger.info(f"Processing {len(articles)} articles...")

        # Get FinBERT scorer (singleton — cached across calls)
        scorer = get_scorer()
        batch_size = 32
        processed_count = 0

        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]

            # ── NER: extract stock mentions ───────────
            for article in batch:
                text = f"{article.get('title', '')} {article.get('body', '')}"
                mentions = extract_stock_mentions(text)
                article["_mentions"] = mentions

            # ── FinBERT: batch sentiment scoring ──────
            texts = [
                f"{art.get('title', '')} {art.get('body', '')}".strip()
                for art in batch
            ]
            sentiments = scorer.score_batch(texts)

            # ── Update MongoDB documents ──────────────
            for article, sentiment in zip(batch, sentiments):
                try:
                    await collection.update_one(
                        {"_id": article["_id"]},
                        {
                            "$set": {
                                "stock_mentions": article["_mentions"],
                                "sentiment": sentiment.to_dict(),
                                "processed": True,
                                "processed_at": datetime.now(timezone.utc),
                            }
                        },
                    )
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Failed to update article {article['_id']}: {e}")

            logger.info(
                f"Processed batch {i // batch_size + 1}: "
                f"{len(batch)} articles"
            )

        return processed_count

    try:
        count = _run_async(_process())
        result = {
            "status": "success",
            "articles_processed": count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"Sentiment processing complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Sentiment processing failed: {e}")
        return {"status": "error", "error": str(e)}


@celery_app.task(name="app.tasks.sentiment_tasks.task_full_pipeline", bind=True)
def task_full_pipeline(self) -> dict:
    """
    Full pipeline: scrape → process sentiment.

    Returns combined result from both steps.
    """
    logger.info("Starting full sentiment pipeline...")

    scrape_result = task_scrape_news()
    process_result = task_process_sentiment()

    return {
        "status": "success",
        "scrape": scrape_result,
        "process": process_result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
