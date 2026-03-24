-- ================================================================
-- Indian Stock Intelligence Platform — PostgreSQL + TimescaleDB
-- ================================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ─── Stocks Master Table ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS stocks (
    id              SERIAL PRIMARY KEY,
    symbol          VARCHAR(20)  NOT NULL UNIQUE,
    name            VARCHAR(200) NOT NULL,
    sector          VARCHAR(100),
    market_cap      BIGINT,
    is_nifty50      BOOLEAN      NOT NULL DEFAULT TRUE,
    listed_date     DATE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stocks_symbol ON stocks (symbol);
CREATE INDEX idx_stocks_sector ON stocks (sector);

-- ─── OHLCV Price Data (Hypertable) ──────────────────────────────
CREATE TABLE IF NOT EXISTS prices (
    id              BIGSERIAL,
    stock_id        INT          NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    ts              TIMESTAMPTZ  NOT NULL,
    open            NUMERIC(12, 2),
    high            NUMERIC(12, 2),
    low             NUMERIC(12, 2),
    close           NUMERIC(12, 2),
    adj_close       NUMERIC(12, 2),
    volume          BIGINT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (stock_id, ts)
);

-- Convert prices to a TimescaleDB hypertable
SELECT create_hypertable('prices', 'ts', migrate_data => true, if_not_exists => true);

CREATE INDEX idx_prices_stock_ts ON prices (stock_id, ts DESC);

-- ─── Risk Scores ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS risk_scores (
    id              BIGSERIAL    PRIMARY KEY,
    stock_id        INT          NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    ts              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    volatility_30d  NUMERIC(10, 6),
    beta            NUMERIC(10, 6),
    sharpe_ratio    NUMERIC(10, 6),
    var_95          NUMERIC(10, 6),
    composite_score NUMERIC(5, 2),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (stock_id, ts)
);

CREATE INDEX idx_risk_stock_ts ON risk_scores (stock_id, ts DESC);

-- ─── RBI Macro Indicators ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS rbi_indicators (
    id                BIGSERIAL    PRIMARY KEY,
    ts                TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    repo_rate         NUMERIC(5, 2),
    reverse_repo_rate NUMERIC(5, 2),
    cpi_yoy           NUMERIC(5, 2),
    gdp_growth        NUMERIC(5, 2),
    forex_reserves    NUMERIC(14, 2),   -- in crores
    indicator_source  VARCHAR(200),
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rbi_ts ON rbi_indicators (ts DESC);

-- ─── News Articles ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS news_articles (
    id              BIGSERIAL    PRIMARY KEY,
    stock_id        INT          REFERENCES stocks(id) ON DELETE SET NULL,
    published_at    TIMESTAMPTZ,
    headline        VARCHAR(500) NOT NULL,
    summary         TEXT,
    sentiment_score NUMERIC(4, 3),  -- range -1.000 to +1.000
    source_url      VARCHAR(1000),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_news_published ON news_articles (published_at DESC);
CREATE INDEX idx_news_stock     ON news_articles (stock_id);

-- ─── Trigger: Auto-update updated_at ────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_stocks_updated
    BEFORE UPDATE ON stocks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
