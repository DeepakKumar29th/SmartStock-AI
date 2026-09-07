-- ============================================================
-- SMARTSTOCK AI
-- STEP 6.1 — CREATE OPERATIONAL INVENTORY UPDATES TABLE
-- Dedicated schema: app
-- Table: app.inventory_updates
-- Ensures zero modification to core.fact_daily_sales & ML tables
-- ============================================================

CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.inventory_updates (
    update_id       BIGSERIAL PRIMARY KEY,
    dt              DATE NOT NULL,
    store_id        INTEGER NOT NULL REFERENCES core.dim_store(store_id) ON DELETE RESTRICT,
    product_id      INTEGER NOT NULL REFERENCES core.dim_product(product_id) ON DELETE RESTRICT,
    sale_amount     NUMERIC(10, 2) NOT NULL CHECK (sale_amount >= 0),
    stock_status    VARCHAR(20) NOT NULL CHECK (stock_status IN ('In Stock', 'Low Stock', 'Out of Stock')),
    discount        NUMERIC(5, 2) DEFAULT 0.00 CHECK (discount >= 0.00 AND discount <= 100.00),
    holiday_flag    INTEGER DEFAULT 0 CHECK (holiday_flag IN (0, 1)),
    activity_flag   INTEGER DEFAULT 0 CHECK (activity_flag IN (0, 1)),
    notes           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_inventory_update UNIQUE (dt, store_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_updates_created_at ON app.inventory_updates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_updates_store_prod ON app.inventory_updates(store_id, product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_updates_dt ON app.inventory_updates(dt DESC);
