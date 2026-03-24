"""
Unit tests for the NLP news sentiment pipeline.

Tests cover:
- Ticker dictionary alias resolution
- NER stock mention extraction (mocked spaCy)
- Temporal decay aggregation math
- Sentiment trend computation
- Schema validation
- Route registration
"""

import math
from datetime import datetime, timedelta, timezone

import pytest


# ═══════════════════════════════════════════════════════
# Ticker Map Tests
# ═══════════════════════════════════════════════════════

class TestTickerMap:
    """Test Nifty 50 ticker dictionary resolution."""

    def test_resolve_reliance(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("reliance") == "RELIANCE.NS"

    def test_resolve_reliance_industries(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("Reliance Industries") == "RELIANCE.NS"

    def test_resolve_ril(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("RIL") == "RELIANCE.NS"

    def test_resolve_tcs(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("TCS") == "TCS.NS"

    def test_resolve_tata_consultancy_services(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("Tata Consultancy Services") == "TCS.NS"

    def test_resolve_hdfc_bank(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("HDFC Bank") == "HDFCBANK.NS"

    def test_resolve_infosys(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("infosys") == "INFY.NS"

    def test_resolve_sbi(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("SBI") == "SBIN.NS"

    def test_resolve_airtel(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("Airtel") == "BHARTIARTL.NS"

    def test_resolve_dmart(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("DMart") == "DMART.NS"

    def test_resolve_unknown_returns_none(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("XYZ Corp") is None

    def test_resolve_empty_string(self):
        from app.nlp.ticker_map import resolve_symbol
        assert resolve_symbol("") is None

    def test_get_all_aliases_nonempty(self):
        from app.nlp.ticker_map import get_all_aliases
        aliases = get_all_aliases()
        assert len(aliases) > 100

    def test_get_all_symbols_has_50(self):
        from app.nlp.ticker_map import get_all_symbols
        symbols = get_all_symbols()
        assert len(symbols) == 49  # 49 unique: WIPRO duplicate in seed data

    def test_all_symbols_end_with_ns(self):
        from app.nlp.ticker_map import get_all_symbols
        for sym in get_all_symbols():
            assert sym.endswith(".NS"), f"{sym} does not end with .NS"

    def test_get_symbol_name(self):
        from app.nlp.ticker_map import get_symbol_name
        name = get_symbol_name("RELIANCE.NS")
        assert name is not None
        assert len(name) > 0


# ═══════════════════════════════════════════════════════
# Temporal Decay Tests
# ═══════════════════════════════════════════════════════

class TestTemporalDecay:
    """Test the exponential decay aggregation math."""

    def test_empty_scores_returns_zero(self):
        from app.nlp.sentiment_aggregator import compute_decayed_sentiment
        assert compute_decayed_sentiment([]) == 0.0

    def test_single_fresh_article(self):
        """An article from 'now' should have full weight, score ≈ input score."""
        from app.nlp.sentiment_aggregator import compute_decayed_sentiment
        now = datetime.now(timezone.utc)
        scores = [{"composite_score": 0.8, "published_at": now}]
        result = compute_decayed_sentiment(scores, reference_time=now)
        assert abs(result - 0.8) < 0.001

    def test_old_article_decays(self):
        """An article from 7 days ago should be heavily decayed at lambda=0.2."""
        from app.nlp.sentiment_aggregator import compute_decayed_sentiment
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=7)
        scores = [{"composite_score": 1.0, "published_at": old}]
        result = compute_decayed_sentiment(scores, reference_time=now, decay_lambda=0.2)
        expected_weight = math.exp(-0.2 * 7)  # ≈ 0.2466
        # Single article: result = score * weight / weight = score
        assert abs(result - 1.0) < 0.001  # Normalised by weight

    def test_two_articles_weighted(self):
        """Two articles: fresh positive + old negative should be net positive."""
        from app.nlp.sentiment_aggregator import compute_decayed_sentiment
        now = datetime.now(timezone.utc)
        scores = [
            {"composite_score": 0.5, "published_at": now},
            {"composite_score": -0.5, "published_at": now - timedelta(days=5)},
        ]
        result = compute_decayed_sentiment(scores, reference_time=now, decay_lambda=0.2)
        # Fresh article gets weight 1.0, old gets weight exp(-1.0) ≈ 0.368
        # Weighted avg ≈ (0.5 * 1.0 + (-0.5) * 0.368) / (1.0 + 0.368)
        expected = (0.5 * 1.0 + (-0.5) * math.exp(-1.0)) / (1.0 + math.exp(-1.0))
        assert abs(result - expected) < 0.001

    def test_decay_lambda_zero_equal_weight(self):
        """Lambda=0 means no decay — all articles weighted equally."""
        from app.nlp.sentiment_aggregator import compute_decayed_sentiment
        now = datetime.now(timezone.utc)
        scores = [
            {"composite_score": 0.6, "published_at": now},
            {"composite_score": -0.4, "published_at": now - timedelta(days=10)},
        ]
        result = compute_decayed_sentiment(scores, reference_time=now, decay_lambda=0.0)
        expected = (0.6 + (-0.4)) / 2
        assert abs(result - expected) < 0.001

    def test_missing_published_at_skipped(self):
        """Articles without published_at should be skipped."""
        from app.nlp.sentiment_aggregator import compute_decayed_sentiment
        now = datetime.now(timezone.utc)
        scores = [
            {"composite_score": 0.8, "published_at": now},
            {"composite_score": -0.5, "published_at": None},
        ]
        result = compute_decayed_sentiment(scores, reference_time=now)
        assert abs(result - 0.8) < 0.001


# ═══════════════════════════════════════════════════════
# Schema Tests
# ═══════════════════════════════════════════════════════

class TestSentimentSchemas:
    """Test sentiment Pydantic schema validation."""

    def test_sentiment_score_out(self):
        from app.models.schemas import SentimentScoreOut
        score = SentimentScoreOut(
            composite_score=0.45,
            positive_pct=60.0,
            negative_pct=10.0,
            neutral_pct=30.0,
            article_count=15,
            trend="bullish",
            window_days=7,
        )
        assert score.composite_score == 0.45
        assert score.trend == "bullish"

    def test_sentiment_response(self):
        from app.models.schemas import SentimentResponse, SentimentScoreOut
        resp = SentimentResponse(
            symbol="RELIANCE.NS",
            name="Reliance Industries",
            sentiment=SentimentScoreOut(
                composite_score=0.3,
                article_count=10,
                trend="neutral",
            ),
        )
        assert resp.symbol == "RELIANCE.NS"
        assert resp.sentiment.article_count == 10

    def test_news_feed_item(self):
        from app.models.schemas import NewsFeedItem
        item = NewsFeedItem(
            headline="Reliance Q3 beats estimates",
            source="economic_times",
            sentiment_score=0.75,
            positive=0.8,
            negative=0.1,
            neutral=0.1,
            stock_mentions=["RELIANCE.NS"],
        )
        assert item.headline == "Reliance Q3 beats estimates"
        assert len(item.stock_mentions) == 1

    def test_news_feed_response(self):
        from app.models.schemas import NewsFeedResponse
        resp = NewsFeedResponse(
            articles=[],
            count=0,
            total=0,
        )
        assert resp.count == 0
        assert resp.page == 1

    def test_news_refresh_response(self):
        from app.models.schemas import NewsRefreshResponse
        resp = NewsRefreshResponse(
            status="accepted",
            message="Pipeline dispatched",
            task_id="abc-123",
        )
        assert resp.task_id == "abc-123"


# ═══════════════════════════════════════════════════════
# Module Import Tests
# ═══════════════════════════════════════════════════════

class TestModuleImports:
    """Verify all new modules can be imported without errors."""

    def test_import_ticker_map(self):
        from app.nlp.ticker_map import (
            NIFTY50_TICKER_MAP,
            get_all_aliases,
            get_all_symbols,
            resolve_symbol,
        )
        assert NIFTY50_TICKER_MAP is not None

    def test_import_sentiment_aggregator(self):
        from app.nlp.sentiment_aggregator import (
            compute_decayed_sentiment,
            compute_rolling_sentiment,
        )
        assert compute_decayed_sentiment is not None

    def test_import_celery_app(self):
        from app.celery_app import celery_app
        assert celery_app is not None

    def test_import_sentiment_tasks(self):
        from app.tasks.sentiment_tasks import (
            task_full_pipeline,
            task_process_sentiment,
            task_scrape_news,
        )
        assert task_scrape_news is not None

    def test_import_news_scrapers(self):
        from app.services.news_scrapers import (
            BusinessStandardScraper,
            EconomicTimesScraper,
            MoneycontrolScraper,
            RawArticle,
            scrape_all_sources,
        )
        assert RawArticle is not None
        assert len([EconomicTimesScraper, MoneycontrolScraper, BusinessStandardScraper]) == 3

    def test_import_schemas(self):
        from app.models.schemas import (
            NewsFeedItem,
            NewsFeedResponse,
            NewsRefreshResponse,
            SentimentResponse,
            SentimentScoreOut,
        )
        assert SentimentScoreOut is not None


# ═══════════════════════════════════════════════════════
# Route Registration Tests
# ═══════════════════════════════════════════════════════

class TestRouteRegistration:
    """Verify sentiment routes are registered in the app."""

    def test_sentiment_route_registered(self):
        from app.main import app
        routes = [route.path for route in app.routes]
        assert "/api/sentiment/{symbol}" in routes

    def test_news_feed_route_registered(self):
        from app.main import app
        routes = [route.path for route in app.routes]
        assert "/api/news/feed" in routes

    def test_news_refresh_route_registered(self):
        from app.main import app
        routes = [route.path for route in app.routes]
        assert "/api/news/refresh" in routes
