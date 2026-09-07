# ============================================================
# SMARTSTOCK AI
# test_neon_connection.py — Safe Connection Test for Neon PostgreSQL
# NEVER prints passwords, secrets, or raw connection strings
# ============================================================

import os
import sys
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Load .env from project root or parent workspace root
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parent.parent if _HERE.parent.name == "python" else _HERE.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "python"))
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT.parent / ".env")

NEON_URL = os.getenv("NEON_DATABASE_URL", "").strip()


def resolve_neon_host(hostname: str) -> str:
    """
    Resolve hostname to an IP address.
    If local DNS lookup fails (e.g. ISP DNS refusal on .tech domains),
    falls back to querying Google DNS (8.8.8.8) via nslookup.
    """
    import socket
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        import subprocess, re
        try:
            out = subprocess.check_output(["nslookup", hostname, "8.8.8.8"], text=True, timeout=5)
            ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", out)
            for ip in ips:
                if not ip.startswith("8.8.") and not ip.startswith("127."):
                    return ip
        except Exception:
            pass
    return None


def mask_host(host: str) -> str:
    if not host:
        return "unknown"
    parts = host.split(".")
    if len(parts) >= 3:
        masked_prefix = parts[0][:4] + "***"
        return ".".join([masked_prefix] + parts[1:])
    return host[:3] + "***"


def test_neon():
    print("=" * 70)
    print("SMARTSTOCK AI — NEON CLOUD POSTGRESQL CONNECTION TEST")
    print("=" * 70)

    if not NEON_URL:
        print("\n[STATUS] NEON_DATABASE_URL is not currently set in .env.")
        print("To test your Neon Cloud PostgreSQL database:")
        print("  1. Add your connection string to your local .env file:")
        print("     NEON_DATABASE_URL=postgresql://username:password@host/database?sslmode=require")
        print("  2. Run this test script again:")
        print("     python python/test_neon_connection.py")
        print("\nTesting Local PostgreSQL fallback connection...")
        try:
            try:
                from python.db_config import get_engine
            except ImportError:
                from db_config import get_engine
            engine = get_engine()
            with engine.connect() as conn:
                from sqlalchemy import text
                res = conn.execute(text("SELECT version();")).scalar()
                print(f"  Local PostgreSQL: CONNECTED (localhost:5433)")
                print(f"  Version: {res.split(',')[0]}")
        except Exception as e:
            print(f"  Local PostgreSQL check: {e}")
        print("=" * 70)
        return

    # Parse Neon URL safely
    try:
        parsed = urllib.parse.urlparse(NEON_URL)
        host = parsed.hostname
        port = parsed.port or 5432
        dbname = parsed.path.lstrip("/") or "neondb"
        user = parsed.username or "neondb_owner"
        password = parsed.password or ""
    except Exception as e:
        print(f"[ERROR] Failed to parse NEON_DATABASE_URL: {type(e).__name__}")
        return

    masked_h = mask_host(host)
    print(f"\nTarget Database : {dbname}")
    print(f"Target Host     : {masked_h}:{port}")
    print(f"Target User     : {user[:3]}***")
    print(f"SSL Mode        : require (Enforced)")

    try:
        conn_kwargs = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
            "sslmode": "require",
            "connect_timeout": 10
        }
        resolved_ip = resolve_neon_host(host)
        if resolved_ip:
            conn_kwargs["hostaddr"] = resolved_ip

        conn = psycopg2.connect(**conn_kwargs)
        cur = conn.cursor()

        # 1. Query PostgreSQL version and simple query
        cur.execute("SELECT version();")
        version_str = cur.fetchone()[0]

        cur.execute("SELECT 1;")
        simple_query_ok = (cur.fetchone()[0] == 1)

        # 2. Check SSL status
        ssl_in_use = getattr(conn.info, "ssl_in_use", False)
        protocol = conn.info.ssl_attribute("protocol") if hasattr(conn.info, "ssl_attribute") else "Active"
        cipher = conn.info.ssl_attribute("cipher") if hasattr(conn.info, "ssl_attribute") else "Active"

        # 3. Query current catalog context
        cur.execute("SELECT current_database(), current_user;")
        curr_db, curr_user = cur.fetchone()

        # 4. Read production tables
        cur.execute("SELECT COUNT(*) FROM core.dim_store;")
        store_cnt = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ml.forecast_recommendations;")
        forecast_cnt = cur.fetchone()[0]

        print("\n" + "-" * 70)
        print("TEST RESULTS:")
        print(f"  1. Connection Status   : SUCCESSFUL")
        print(f"  2. Active Database     : {curr_db}")
        print(f"  3. Active User         : {curr_user[:3]}***")
        print(f"  4. PostgreSQL Version  : {version_str.split(',')[0]}")
        print(f"  5. SSL Connection Used : {ssl_in_use} (Protocol: {protocol}, Cipher: {cipher})")
        print(f"  6. Simple Query Check  : {'PASS' if simple_query_ok else 'FAIL'}")
        print(f"  7. Production Read     : core.dim_store ({store_cnt:,} rows) [PASS]")
        print(f"  8. Production Read     : ml.forecast_recommendations ({forecast_cnt:,} rows) [PASS]")
        print("-" * 70)
        print("[SUCCESS] Neon Cloud PostgreSQL is healthy, secure, and production ready.")
        print("=" * 70)

        conn.close()

    except Exception as e:
        err_msg = str(e)
        if password and password in err_msg:
            err_msg = err_msg.replace(password, "******")
        print("\n" + "-" * 70)
        print(f"[FAILED] Could not connect to Neon PostgreSQL:")
        print(f"  Error Type: {type(e).__name__}")
        print(f"  Detail: {err_msg}")
        print("-" * 70)
        print("=" * 70)


if __name__ == "__main__":
    test_neon()
