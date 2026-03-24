"""
Smoke tests for the GPR (Geopolitical Risk) Scoring Engine.

Tests:
1. Module imports work without errors
2. Pydantic schemas validate sample data
3. Sector mapping covers all Nifty 50 sectors
4. Revenue exposure dict covers all 50 symbols
5. Score formula produces correct output for known inputs
6. New routes are registered in the FastAPI app
"""

import pytest
from datetime import datetime


# ═══════════════════════════════════════════════════════
# Module Import Tests
# ═══════════════════════════════════════════════════════

class TestGPRImports:
    """Verify all GPR modules can be imported."""

    def test_import_fred_client(self):
        from app.services.fred_client import (
            fetch_and_store_gpr,
            normalize_gpr_series,
        )
        assert fetch_and_store_gpr is not None
        assert normalize_gpr_series is not None

    def test_import_gpr_engine(self):
        from app.services.gpr_engine import (
            compute_all_gpr_scores,
            compute_gpr_score,
            get_gpr_heatmap,
            get_gpr_sector,
            get_revenue_exposure,
            get_sector_baseline,
            get_stock_gpr_history,
        )
        assert compute_all_gpr_scores is not None
        assert compute_gpr_score is not None

    def test_import_gpr_models(self):
        from app.models.sql_models import GPRIndex, GPRScore
        assert GPRIndex.__tablename__ == "gpr_index"
        assert GPRScore.__tablename__ == "gpr_scores"

    def test_import_gpr_schemas(self):
        from app.models.schemas import (
            GPRHeatmapItem,
            GPRHeatmapResponse,
            GPRScoreOut,
            GPRSectorAggregate,
            GPRStockResponse,
        )
        assert GPRScoreOut is not None
        assert GPRHeatmapResponse is not None

    def test_import_scheduler_gpr_job(self):
        from app.jobs.scheduler import job_refresh_gpr_scores
        assert job_refresh_gpr_scores is not None


# ═══════════════════════════════════════════════════════
# Schema Validation Tests
# ═══════════════════════════════════════════════════════

class TestGPRSchemas:
    """Verify GPR Pydantic schemas validate correctly."""

    def test_gpr_score_out(self):
        from app.models.schemas import GPRScoreOut
        score = GPRScoreOut(
            ts=datetime(2024, 3, 1),
            gpr_sector="IT",
            sector_baseline=1.6,
            gpr_global_norm=0.75,
            revenue_exposure_pct=95.0,
            revenue_exposure_fac=1.45,
            gpr_score=1.74,
            percentile_rank=92.0,
        )
        assert score.gpr_sector == "IT"
        assert score.gpr_score == 1.74

    def test_gpr_stock_response(self):
        from app.models.schemas import GPRStockResponse
        resp = GPRStockResponse(
            symbol="TCS.NS",
            name="Tata Consultancy Services",
            sector="Information Technology",
            gpr_sector="IT",
            current_score=None,
            history=[],
            history_count=0,
        )
        assert resp.symbol == "TCS.NS"
        assert resp.history_count == 0

    def test_gpr_heatmap_item(self):
        from app.models.schemas import GPRHeatmapItem
        item = GPRHeatmapItem(
            symbol="RELIANCE.NS",
            name="Reliance Industries",
            sector="Energy",
            gpr_sector="Energy",
            gpr_score=1.35,
            percentile_rank=85.0,
            sector_baseline=1.8,
            revenue_exposure_pct=35.0,
        )
        assert item.gpr_sector == "Energy"

    def test_gpr_sector_aggregate(self):
        from app.models.schemas import GPRSectorAggregate
        agg = GPRSectorAggregate(
            gpr_sector="IT",
            avg_gpr_score=1.65,
            max_gpr_score=1.85,
            min_gpr_score=1.45,
            stock_count=5,
            baseline=1.6,
        )
        assert agg.stock_count == 5
        assert agg.baseline == 1.6

    def test_gpr_heatmap_response(self):
        from app.models.schemas import GPRHeatmapResponse
        resp = GPRHeatmapResponse(
            stocks=[],
            sectors=[],
            total_stocks=0,
            last_updated=None,
        )
        assert resp.total_stocks == 0


# ═══════════════════════════════════════════════════════
# Sector & Revenue Mapping Tests
# ═══════════════════════════════════════════════════════

class TestSectorMapping:
    """Verify sector classification covers all Nifty 50 sectors."""

    def test_all_known_sectors_mapped(self):
        from app.services.gpr_engine import SECTOR_MAPPING

        # All sector values present in the Nifty 50 seed data
        nifty_sectors = [
            "Energy", "Information Technology", "Financial Services",
            "FMCG", "Automobile", "Healthcare", "Metals & Mining",
            "Construction", "Construction Materials", "Infrastructure",
            "Power", "Telecommunication", "Consumer Durables",
            "Consumer Services", "Diversified",
        ]
        for sector in nifty_sectors:
            assert sector in SECTOR_MAPPING, f"Sector '{sector}' not in SECTOR_MAPPING"

    def test_sector_baselines_complete(self):
        from app.services.gpr_engine import SECTOR_BASELINES, SECTOR_MAPPING

        # Every mapped GPR sector must have a baseline
        gpr_sectors = set(SECTOR_MAPPING.values())
        for gpr_sector in gpr_sectors:
            assert gpr_sector in SECTOR_BASELINES, (
                f"GPR sector '{gpr_sector}' missing from SECTOR_BASELINES"
            )

    def test_energy_highest_baseline(self):
        from app.services.gpr_engine import SECTOR_BASELINES
        assert SECTOR_BASELINES["Energy"] == 1.8

    def test_fmcg_lowest_baseline(self):
        from app.services.gpr_engine import SECTOR_BASELINES
        assert SECTOR_BASELINES["FMCG"] == 0.7


class TestRevenueExposure:
    """Verify revenue exposure covers all 50 symbols."""

    def test_coverage(self):
        from app.services.gpr_engine import REVENUE_EXPOSURE

        # Key symbols that must be present
        critical_symbols = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
            "ICICIBANK.NS", "HINDUNILVR.NS", "SBIN.NS", "TATAMOTORS.NS",
        ]
        for sym in critical_symbols:
            assert sym in REVENUE_EXPOSURE, f"Symbol '{sym}' missing from REVENUE_EXPOSURE"

    def test_it_stocks_high_exposure(self):
        from app.services.gpr_engine import REVENUE_EXPOSURE
        # IT stocks should have > 80% international revenue
        for sym in ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"]:
            assert REVENUE_EXPOSURE[sym] >= 80.0, (
                f"{sym} should have high international exposure"
            )

    def test_banking_low_exposure(self):
        from app.services.gpr_engine import REVENUE_EXPOSURE
        # Banking stocks should have < 10% international revenue
        for sym in ["HDFCBANK.NS", "SBIN.NS", "KOTAKBANK.NS"]:
            assert REVENUE_EXPOSURE[sym] <= 10.0, (
                f"{sym} should have low international exposure"
            )


# ═══════════════════════════════════════════════════════
# Score Computation Tests
# ═══════════════════════════════════════════════════════

class TestScoreComputation:
    """Verify GPR score formula produces expected results."""

    def test_score_formula(self):
        from app.services.gpr_engine import compute_gpr_score
        # sector_baseline=1.8, gpr_global=0.8, gpr_india=0.6, rev_pct=35
        # composite_norm = 0.7*0.8 + 0.3*0.6 = 0.56 + 0.18 = 0.74
        # rev_factor = 0.5 + 35/100 = 0.85
        # score = 1.8 * 0.74 * 0.85 = 1.1322
        score = compute_gpr_score(1.8, 0.8, 0.6, 35.0)
        assert abs(score - 1.1322) < 0.001

    def test_score_zero_gpr(self):
        from app.services.gpr_engine import compute_gpr_score
        # If GPR norms are 0, score should be 0
        score = compute_gpr_score(1.8, 0.0, 0.0, 35.0)
        assert score == 0.0

    def test_revenue_factor(self):
        from app.services.gpr_engine import compute_revenue_factor
        assert compute_revenue_factor(0.0) == 0.5
        assert compute_revenue_factor(100.0) == 1.5
        assert compute_revenue_factor(50.0) == 1.0

    def test_get_gpr_sector(self):
        from app.services.gpr_engine import get_gpr_sector
        assert get_gpr_sector("Energy") == "Energy"
        assert get_gpr_sector("Information Technology") == "IT"
        assert get_gpr_sector("Financial Services") == "Banking"
        assert get_gpr_sector(None) == "Diversified"


# ═══════════════════════════════════════════════════════
# Route Registration Tests
# ═══════════════════════════════════════════════════════

class TestRouteRegistration:
    """Verify GPR routes are registered in the FastAPI app."""

    def test_gpr_routes_exist(self):
        from app.main import app
        routes = [route.path for route in app.routes]
        assert "/api/gpr/stock/{symbol}" in routes, "GPR stock endpoint not registered"
        assert "/api/gpr/heatmap" in routes, "GPR heatmap endpoint not registered"
        assert "/api/gpr/refresh" in routes, "GPR refresh endpoint not registered"


# ═══════════════════════════════════════════════════════
# FRED Client Tests
# ═══════════════════════════════════════════════════════

class TestFREDClient:
    """Verify FRED client utilities."""

    def test_normalize_gpr_series(self):
        import pandas as pd
        from app.services.fred_client import normalize_gpr_series

        series = pd.Series([100, 150, 200, 250, 300])
        normalized = normalize_gpr_series(series)
        assert normalized.iloc[0] == 0.0
        assert normalized.iloc[-1] == 1.0
        assert all(0 <= v <= 1 for v in normalized)

    def test_normalize_constant_series(self):
        import pandas as pd
        from app.services.fred_client import normalize_gpr_series

        series = pd.Series([100, 100, 100])
        normalized = normalize_gpr_series(series)
        assert all(v == 0.5 for v in normalized)

    def test_synthetic_data_generation(self):
        from app.services.fred_client import _generate_synthetic_gpr

        data = _generate_synthetic_gpr()
        assert "global" in data
        assert "india" in data
        assert len(data["global"]) == 75
        assert len(data["india"]) == 75
