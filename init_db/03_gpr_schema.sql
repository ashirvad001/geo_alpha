-- ================================================================
-- Geopolitical Risk (GPR) Scoring Engine — Schema
-- ================================================================

-- ─── GPR Index (monthly FRED data) ──────────────────────────────
CREATE TABLE IF NOT EXISTS gpr_index (
    id              BIGSERIAL,
    ts              TIMESTAMPTZ  NOT NULL,
    gpr_global      NUMERIC(10, 4),       -- Caldara-Iacoviello GPR Global
    gpr_india       NUMERIC(10, 4),       -- India-specific GPRI_IN
    gpr_global_norm NUMERIC(8, 6),        -- Normalized 0–1
    gpr_india_norm  NUMERIC(8, 6),        -- Normalized 0–1
    source          VARCHAR(50)  NOT NULL DEFAULT 'FRED',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (ts)
);

-- Convert to hypertable
SELECT create_hypertable('gpr_index', 'ts', migrate_data => true, if_not_exists => true);

CREATE INDEX idx_gpr_index_ts ON gpr_index (ts DESC);

-- ─── Per-Stock GPR Scores ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS gpr_scores (
    id                    BIGSERIAL    PRIMARY KEY,
    stock_id              INT          NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    ts                    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    gpr_sector            VARCHAR(50),
    sector_baseline       NUMERIC(4, 2),
    gpr_global_norm       NUMERIC(8, 6),
    revenue_exposure_pct  NUMERIC(5, 2),        -- International revenue %
    revenue_exposure_fac  NUMERIC(6, 4),         -- 0.5 + (pct/100)
    gpr_score             NUMERIC(8, 4),         -- Final composite score
    percentile_rank       NUMERIC(5, 2),         -- 0–100
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (stock_id, ts)
);

CREATE INDEX idx_gpr_scores_stock_ts ON gpr_scores (stock_id, ts DESC);
CREATE INDEX idx_gpr_scores_ts       ON gpr_scores (ts DESC);
CREATE INDEX idx_gpr_scores_score    ON gpr_scores (gpr_score DESC);
