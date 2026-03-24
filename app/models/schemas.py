"""
Pydantic v2 schemas for API request / response serialization.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════
# Stock Schemas
# ═══════════════════════════════════════════════════════

class StockBase(BaseModel):
    symbol: str
    name: str
    sector: str | None = None
    is_nifty50: bool = True


class StockOut(StockBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    market_cap: int | None = None
    listed_date: date | None = None


# ═══════════════════════════════════════════════════════
# Price Schemas
# ═══════════════════════════════════════════════════════

class PriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    adj_close: float | None = None
    volume: int | None = None


class PriceHistoryResponse(BaseModel):
    symbol: str
    count: int
    data: list[PriceOut]


# ═══════════════════════════════════════════════════════
# RBI Indicator Schemas
# ═══════════════════════════════════════════════════════

class RBIIndicatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ts: datetime
    repo_rate: float | None = None
    reverse_repo_rate: float | None = None
    cpi_yoy: float | None = None
    gdp_growth: float | None = None
    forex_reserves: float | None = None
    indicator_source: str | None = None


class RBILatestResponse(BaseModel):
    latest: RBIIndicatorOut | None = None
    history_count: int = 0


# ═══════════════════════════════════════════════════════
# Risk Score Schemas
# ═══════════════════════════════════════════════════════

class RiskScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    volatility_30d: float | None = None
    beta: float | None = None
    sharpe_ratio: float | None = None
    var_95: float | None = None
    composite_score: float | None = None


# ═══════════════════════════════════════════════════════
# News Schemas
# ═══════════════════════════════════════════════════════

class NewsArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    headline: str
    summary: str | None = None
    published_at: datetime | None = None
    sentiment_score: float | None = None
    source_url: str | None = None


# ═══════════════════════════════════════════════════════
# Data Refresh Schemas
# ═══════════════════════════════════════════════════════

class RefreshRequest(BaseModel):
    symbols: list[str] | None = Field(
        default=None,
        description="Specific symbols to refresh. If None, refreshes all Nifty 50.",
    )
    include_rbi: bool = Field(
        default=True,
        description="Whether to also refresh RBI indicators.",
    )


class RefreshResponse(BaseModel):
    status: str
    message: str
    stocks_updated: int = 0
    rbi_updated: bool = False


# ═══════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════

class HealthCheck(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    postgres: str = "unknown"
    mongo: str = "unknown"
    redis: str = "unknown"


# ═══════════════════════════════════════════════════════
# GPR (Geopolitical Risk) Schemas
# ═══════════════════════════════════════════════════════

class GPRScoreOut(BaseModel):
    """Single GPR score record."""
    model_config = ConfigDict(from_attributes=True)

    ts: datetime
    gpr_sector: str | None = None
    sector_baseline: float | None = None
    gpr_global_norm: float | None = None
    revenue_exposure_pct: float | None = None
    revenue_exposure_fac: float | None = None
    gpr_score: float | None = None
    percentile_rank: float | None = None


class GPRStockResponse(BaseModel):
    """Response for GET /api/gpr/stock/{symbol}."""
    symbol: str
    name: str
    sector: str | None = None
    gpr_sector: str | None = None
    current_score: GPRScoreOut | None = None
    history: list[GPRScoreOut] = []
    history_count: int = 0


class GPRHeatmapItem(BaseModel):
    """Single stock in the heatmap."""
    symbol: str
    name: str
    sector: str | None = None
    gpr_sector: str | None = None
    gpr_score: float | None = None
    percentile_rank: float | None = None
    sector_baseline: float | None = None
    revenue_exposure_pct: float | None = None


class GPRSectorAggregate(BaseModel):
    """Sector-level GPR aggregate."""
    gpr_sector: str
    avg_gpr_score: float
    max_gpr_score: float
    min_gpr_score: float
    stock_count: int
    baseline: float


class GPRHeatmapResponse(BaseModel):
    """Response for GET /api/gpr/heatmap."""
    stocks: list[GPRHeatmapItem]
    sectors: list[GPRSectorAggregate]
    total_stocks: int
    last_updated: datetime | None = None


# ═══════════════════════════════════════════════════════
# Sentiment Schemas
# ═══════════════════════════════════════════════════════

class SentimentScoreOut(BaseModel):
    """Decayed sentiment score for a stock."""
    composite_score: float = Field(
        ..., description="Decayed composite sentiment in [-1, +1]"
    )
    positive_pct: float = 0.0
    negative_pct: float = 0.0
    neutral_pct: float = 0.0
    article_count: int = 0
    trend: str = Field("neutral", description="bullish / bearish / neutral")
    window_days: int = 7
    last_updated: datetime | None = None


class SentimentResponse(BaseModel):
    """Response for GET /api/sentiment/{symbol}."""
    symbol: str
    name: str | None = None
    sector: str | None = None
    sentiment: SentimentScoreOut


class NewsFeedItem(BaseModel):
    """Single news article in the feed."""
    headline: str
    summary: str | None = None
    source: str | None = None
    source_url: str | None = None
    published_at: datetime | None = None
    sentiment_score: float | None = None
    positive: float | None = None
    negative: float | None = None
    neutral: float | None = None
    sentiment_label: str | None = None
    stock_mentions: list[str] = []


class NewsFeedResponse(BaseModel):
    """Response for GET /api/news/feed."""
    articles: list[NewsFeedItem]
    count: int
    total: int = 0
    page: int = 1
    page_size: int = 20


class NewsRefreshResponse(BaseModel):
    """Response for POST /api/news/refresh."""
    status: str
    message: str
    task_id: str | None = None
