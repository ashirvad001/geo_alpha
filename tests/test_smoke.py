"""
Smoke tests for the Indian Stock Intelligence Platform.

These tests verify:
1. All modules can be imported without errors
2. Pydantic schemas validate sample data correctly
3. FastAPI test client can reach basic endpoints
"""

import pytest


# ═══════════════════════════════════════════════════════
# Module Import Tests
# ═══════════════════════════════════════════════════════

class TestImports:
    """Verify all modules can be imported."""

    def test_import_config(self):
        from app.config import settings
        assert settings.app_name is not None

    def test_import_models(self):
        from app.models.sql_models import (
            Base,
            NewsArticle,
            Price,
            RBIIndicator,
            RiskScore,
            Stock,
        )
        assert Stock.__tablename__ == "stocks"
        assert Price.__tablename__ == "prices"
        assert RiskScore.__tablename__ == "risk_scores"
        assert RBIIndicator.__tablename__ == "rbi_indicators"
        assert NewsArticle.__tablename__ == "news_articles"

    def test_import_schemas(self):
        from app.models.schemas import (
            HealthCheck,
            PriceHistoryResponse,
            PriceOut,
            RBIIndicatorOut,
            RefreshRequest,
            RefreshResponse,
            StockOut,
        )
        assert HealthCheck is not None

    def test_import_services(self):
        from app.services.scraper import fetch_stock_history, refresh_all_nifty50
        from app.services.rbi_parser import parse_and_store_bulletin
        from app.services.risk_engine import compute_risk_scores
        assert fetch_stock_history is not None

    def test_import_scheduler(self):
        from app.jobs.scheduler import configure_scheduler, scheduler
        assert scheduler is not None


# ═══════════════════════════════════════════════════════
# Schema Validation Tests
# ═══════════════════════════════════════════════════════

class TestSchemas:
    """Verify Pydantic schemas validate correctly."""

    def test_health_check_schema(self):
        from app.models.schemas import HealthCheck
        hc = HealthCheck(status="ok", version="1.0.0", postgres="connected", mongo="connected", redis="connected")
        assert hc.status == "ok"
        assert hc.version == "1.0.0"

    def test_refresh_request_defaults(self):
        from app.models.schemas import RefreshRequest
        req = RefreshRequest()
        assert req.symbols is None
        assert req.include_rbi is True

    def test_refresh_request_with_symbols(self):
        from app.models.schemas import RefreshRequest
        req = RefreshRequest(symbols=["RELIANCE.NS", "TCS.NS"], include_rbi=False)
        assert len(req.symbols) == 2
        assert req.include_rbi is False

    def test_price_history_response(self):
        from app.models.schemas import PriceHistoryResponse
        resp = PriceHistoryResponse(symbol="RELIANCE.NS", count=0, data=[])
        assert resp.symbol == "RELIANCE.NS"
        assert resp.count == 0

    def test_rbi_indicator_out(self):
        from datetime import datetime
        from app.models.schemas import RBIIndicatorOut
        rbi = RBIIndicatorOut(
            id=1,
            ts=datetime(2024, 1, 1),
            repo_rate=6.50,
            cpi_yoy=4.87,
        )
        assert rbi.repo_rate == 6.50


# ═══════════════════════════════════════════════════════
# App Creation Test (no DB required)
# ═══════════════════════════════════════════════════════

class TestAppCreation:
    """Verify the FastAPI app object can be created."""

    def test_app_exists(self):
        from app.main import app
        assert app is not None
        assert app.title == "Indian Stock Intelligence Platform"

    def test_routes_registered(self):
        from app.main import app
        routes = [route.path for route in app.routes]
        assert "/health" in routes
        assert "/" in routes
        assert "/api/stocks" in routes
        assert "/api/stocks/{symbol}/history" in routes
        assert "/api/rbi/latest" in routes
        assert "/api/data/refresh" in routes
