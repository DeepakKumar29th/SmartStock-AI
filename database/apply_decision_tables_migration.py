# ============================================================
# SMARTSTOCK AI
# Migration runner for operational decision & alert tables
# ============================================================

import sys
from pathlib import Path

# Add project root and streamlit directory to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "streamlit"))

from sqlalchemy import text
from db_connection import get_engine

def run_migration():
    engine = get_engine()
    sql_file = ROOT / "database" / "STEP 6.2 - CREATE OPERATIONAL DECISION TABLES.sql"
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print(f"Applying migration from {sql_file.name}...")
    with engine.begin() as conn:
        conn.execute(text(sql_content))
    print("Migration applied successfully!")

    # Verify tables existence
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = 'app' AND table_name IN ('replenishment_decisions', 'alert_actions')
            ORDER BY table_name;
        """)).fetchall()
        print(f"Verified tables in PostgreSQL: {res}")

if __name__ == "__main__":
    run_migration()
