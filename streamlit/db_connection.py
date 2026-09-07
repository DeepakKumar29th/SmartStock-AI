# ============================================================
# SMARTSTOCK AI
# db_connection.py — Streamlit Database Connection
# Loads credentials from .env — NEVER hard-codes passwords
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from project root or parent workspace root
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")
load_dotenv(_project_root.parent / ".env")

def _get_neon_url() -> str:
    """
    Retrieve Neon PostgreSQL URL according to connection priority:
    1. Streamlit Cloud Secrets (st.secrets["NEON_DATABASE_URL"])
    2. OS environment variable (NEON_DATABASE_URL from .env or container)
    Returns empty string if not configured.
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "NEON_DATABASE_URL" in st.secrets:
            val = str(st.secrets["NEON_DATABASE_URL"]).strip()
            if val:
                return val
    except Exception:
        pass

    return os.getenv("NEON_DATABASE_URL", "").strip()


def _get_local_param(key: str, default: str = "") -> str:
    """Retrieve configuration parameter checking Streamlit secrets then environment."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            val = str(st.secrets[key]).strip()
            if val:
                return val
    except Exception:
        pass
    return os.getenv(key, default).strip()


def _resolve_neon_host(hostname: str) -> str:
    """Resolve hostname to IP, with fallback to Google DNS if local DNS fails."""
    import socket
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        import subprocess
        try:
            out = subprocess.check_output(["nslookup", hostname, "8.8.8.8"], text=True, timeout=5)
            ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", out)
            for ip in ips:
                if not ip.startswith("8.8.") and not ip.startswith("127."):
                    return ip
        except Exception:
            pass
    return None


def _sanitize_error_msg(error_msg: str) -> str:
    """Sanitize error message to ensure no passwords or credentials appear."""
    import re
    sanitized = re.sub(r"://([^:]+):([^@]+)@", r"://\1:******@", error_msg)
    sanitized = re.sub(r"password=([^\s]+)", r"password=******", sanitized)
    return sanitized


def get_connection_source() -> str:
    """Return a human-readable description of the active connection source (safe, no secrets)."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "NEON_DATABASE_URL" in st.secrets:
            return "Streamlit Secrets (Neon Cloud)"
    except Exception:
        pass

    if os.getenv("NEON_DATABASE_URL", "").strip():
        return "Environment Variable (Neon Cloud)"

    return "Local PostgreSQL (localhost:5433)"


def get_engine():
    """
    Return a SQLAlchemy engine connected to PostgreSQL.
    Connection Priority:
      1. Streamlit Cloud Secrets: st.secrets["NEON_DATABASE_URL"]
      2. Environment Variable   : NEON_DATABASE_URL (from .env or cloud environment)
      3. Local Fallback         : DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
    Raises a sanitized RuntimeError if connection fails (without exposing secrets).
    """
    neon_url = _get_neon_url()

    # ──────────────────────────────────────────────────────────
    # Path A: Neon Cloud PostgreSQL Connection
    # ──────────────────────────────────────────────────────────
    if neon_url:
        url = neon_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        if "sslmode=" not in url:
            delimiter = "&" if "?" in url else "?"
            url = f"{url}{delimiter}sslmode=require"

        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        connect_args = {}
        if parsed.hostname:
            resolved_ip = _resolve_neon_host(parsed.hostname)
            if resolved_ip:
                connect_args["hostaddr"] = resolved_ip

        engine = create_engine(
            url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )

        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            clean_detail = _sanitize_error_msg(str(e))
            raise RuntimeError(
                "Database connection is currently unavailable. Please verify your NEON_DATABASE_URL configuration and network connection.\n"
                f"Detail: {type(e).__name__}: {clean_detail}"
            )

        return engine

    # ──────────────────────────────────────────────────────────
    # Path B: Local PostgreSQL Fallback
    # ──────────────────────────────────────────────────────────
    db_host = _get_local_param("DB_HOST", "localhost")
    db_port = int(_get_local_param("DB_PORT", "5433"))
    db_name = _get_local_param("DB_NAME", "smartstock")
    db_user = _get_local_param("DB_USER", "postgres")
    db_password = _get_local_param("DB_PASSWORD", "")

    if not db_password:
        raise RuntimeError(
            "Neither NEON_DATABASE_URL nor DB_PASSWORD is configured. "
            "Please configure your .env file or Streamlit Secrets."
        )

    connection_string = (
        f"postgresql+psycopg2://"
        f"{db_user}:{db_password}"
        f"@{db_host}:{db_port}/{db_name}"
    )

    engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        clean_detail = _sanitize_error_msg(str(e))
        raise RuntimeError(
            f"Unable to connect to local database at {db_host}:{db_port}/{db_name}. "
            f"Please verify PostgreSQL is running and credentials are correct.\n"
            f"Detail: {type(e).__name__}: {clean_detail}"
        )

    return engine