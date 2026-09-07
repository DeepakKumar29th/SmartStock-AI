-- ============================================================
-- SMARTSTOCK AI
-- STEP 6.2 — CREATE OPERATIONAL DECISION TABLES
-- Dedicated schema: app
-- Tables:
--   1. app.replenishment_decisions (Persistent Manager Reorders)
--   2. app.alert_actions (Persistent Exception Resolution Tracking)
-- Zero modification to core.fact_daily_sales or ML tables
-- ============================================================

CREATE SCHEMA IF NOT EXISTS app;

-- 1. Persistent Replenishment Decisions
CREATE TABLE IF NOT EXISTS app.replenishment_decisions (
    decision_id        BIGSERIAL PRIMARY KEY,
    store_id           INTEGER NOT NULL REFERENCES core.dim_store(store_id) ON DELETE RESTRICT,
    product_id         INTEGER NOT NULL REFERENCES core.dim_product(product_id) ON DELETE RESTRICT,
    decision_date      DATE NOT NULL DEFAULT CURRENT_DATE,
    recommended_qty    NUMERIC(10, 2) NOT NULL CHECK (recommended_qty >= 0),
    approved_qty       NUMERIC(10, 2) NOT NULL CHECK (approved_qty >= 0),
    decision_status    VARCHAR(20) NOT NULL CHECK (decision_status IN ('APPROVED', 'MODIFIED', 'DEFERRED')),
    decision_notes     TEXT,
    decided_by         VARCHAR(50) DEFAULT 'Store Operations',
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_replenishment_decision UNIQUE (decision_date, store_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_repl_decisions_date ON app.replenishment_decisions(decision_date DESC);
CREATE INDEX IF NOT EXISTS idx_repl_decisions_store_prod ON app.replenishment_decisions(store_id, product_id);
CREATE INDEX IF NOT EXISTS idx_repl_decisions_status ON app.replenishment_decisions(decision_status);

-- 2. Persistent Alert Actions
CREATE TABLE IF NOT EXISTS app.alert_actions (
    action_id          BIGSERIAL PRIMARY KEY,
    store_id           INTEGER NOT NULL REFERENCES core.dim_store(store_id) ON DELETE RESTRICT,
    product_id         INTEGER NOT NULL REFERENCES core.dim_product(product_id) ON DELETE RESTRICT,
    alert_severity     VARCHAR(15) NOT NULL,
    action_status      VARCHAR(20) NOT NULL CHECK (action_status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')),
    resolution_notes   TEXT,
    updated_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_alert_action UNIQUE (store_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_alert_actions_status ON app.alert_actions(action_status);
CREATE INDEX IF NOT EXISTS idx_alert_actions_store_prod ON app.alert_actions(store_id, product_id);
