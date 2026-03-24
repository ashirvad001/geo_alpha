"""
SQLAlchemy ORM models for the Stock Intelligence Platform.
Maps to TimescaleDB / PostgreSQL tables defined in init_db/01_schema.sql.
"""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(100))
    market_cap: Mapped[int | None] = mapped_column(BigInteger)
    is_nifty50: Mapped[bool] = mapped_column(Boolean, default=True)
    listed_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prices: Mapped[list["Price"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    risk_scores: Mapped[list["RiskScore"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    gpr_scores: Mapped[list["GPRScore"]] = relationship(back_populates="stock", cascade="all, delete-orphan")
    news_articles: Mapped[list["NewsArticle"]] = relationship(back_populates="stock")

    def __repr__(self) -> str:
        return f"<Stock(symbol={self.symbol!r}, name={self.name!r})>"


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(nullable=False)
    open: Mapped[float | None] = mapped_column(Numeric(12, 2))
    high: Mapped[float | None] = mapped_column(Numeric(12, 2))
    low: Mapped[float | None] = mapped_column(Numeric(12, 2))
    close: Mapped[float | None] = mapped_column(Numeric(12, 2))
    adj_close: Mapped[float | None] = mapped_column(Numeric(12, 2))
    volume: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    stock: Mapped["Stock"] = relationship(back_populates="prices")

    __table_args__ = (
        Index("idx_prices_stock_ts", "stock_id", "ts"),
    )

    def __repr__(self) -> str:
        return f"<Price(stock_id={self.stock_id}, ts={self.ts}, close={self.close})>"


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    volatility_30d: Mapped[float | None] = mapped_column(Numeric(10, 6))
    beta: Mapped[float | None] = mapped_column(Numeric(10, 6))
    sharpe_ratio: Mapped[float | None] = mapped_column(Numeric(10, 6))
    var_95: Mapped[float | None] = mapped_column(Numeric(10, 6))
    composite_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    stock: Mapped["Stock"] = relationship(back_populates="risk_scores")

    def __repr__(self) -> str:
        return f"<RiskScore(stock_id={self.stock_id}, composite={self.composite_score})>"


class RBIIndicator(Base):
    __tablename__ = "rbi_indicators"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ts: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    repo_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reverse_repo_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    cpi_yoy: Mapped[float | None] = mapped_column(Numeric(5, 2))
    gdp_growth: Mapped[float | None] = mapped_column(Numeric(5, 2))
    forex_reserves: Mapped[float | None] = mapped_column(Numeric(14, 2))
    indicator_source: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<RBIIndicator(ts={self.ts}, repo_rate={self.repo_rate})>"


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int | None] = mapped_column(ForeignKey("stocks.id", ondelete="SET NULL"))
    published_at: Mapped[datetime | None] = mapped_column()
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    sentiment_score: Mapped[float | None] = mapped_column(Numeric(4, 3))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    stock: Mapped["Stock | None"] = relationship(back_populates="news_articles")

    def __repr__(self) -> str:
        return f"<NewsArticle(headline={self.headline[:40]!r})>"


# ═══════════════════════════════════════════════════════
# GPR (Geopolitical Risk) Models
# ═══════════════════════════════════════════════════════

class GPRIndex(Base):
    """Monthly Caldara-Iacoviello GPR Index data from FRED."""
    __tablename__ = "gpr_index"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ts: Mapped[datetime] = mapped_column(nullable=False, unique=True)
    gpr_global: Mapped[float | None] = mapped_column(Numeric(10, 4))
    gpr_india: Mapped[float | None] = mapped_column(Numeric(10, 4))
    gpr_global_norm: Mapped[float | None] = mapped_column(Numeric(8, 6))
    gpr_india_norm: Mapped[float | None] = mapped_column(Numeric(8, 6))
    source: Mapped[str] = mapped_column(String(50), default="FRED")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<GPRIndex(ts={self.ts}, global={self.gpr_global}, india={self.gpr_india})>"


class GPRScore(Base):
    """Per-stock Geopolitical Risk score."""
    __tablename__ = "gpr_scores"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    ts: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    gpr_sector: Mapped[str | None] = mapped_column(String(50))
    sector_baseline: Mapped[float | None] = mapped_column(Numeric(4, 2))
    gpr_global_norm: Mapped[float | None] = mapped_column(Numeric(8, 6))
    revenue_exposure_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    revenue_exposure_fac: Mapped[float | None] = mapped_column(Numeric(6, 4))
    gpr_score: Mapped[float | None] = mapped_column(Numeric(8, 4))
    percentile_rank: Mapped[float | None] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    stock: Mapped["Stock"] = relationship(back_populates="gpr_scores")

    __table_args__ = (
        Index("idx_gpr_scores_stock_ts", "stock_id", "ts"),
    )

    def __repr__(self) -> str:
        return f"<GPRScore(stock_id={self.stock_id}, score={self.gpr_score})>"
