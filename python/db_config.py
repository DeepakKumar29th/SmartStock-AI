# ============================================================
# SMARTSTOCK AI
# python/db_config.py — Shared database configuration utility
# All scripts import from here — no passwords in source files
# ============================================================

import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Locate project root (.env is at project root or parent workspace root)
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parent.parent if _HERE.parent.name == "python" else _HERE.parent
load_dotenv(_ROOT / ".env")
load_dotenv(_ROOT.parent / ".env")

def _get_neon_url() -> str:
    """Retrieve Neon URL from Streamlit Secrets or Environment."""
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
    """Retrieve parameter checking Streamlit secrets then environment."""
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


def _sanitize_error_msg(error_msg: str) -> str:
    """Sanitize error message to ensure no passwords or credentials appear."""
    import re
    sanitized = re.sub(r"://([^:]+):([^@]+)@", r"://\1:******@", error_msg)
    sanitized = re.sub(r"password=([^\s]+)", r"password=******", sanitized)
    return sanitized


def _get_cfg():
    neon_url = _get_neon_url()
    if neon_url:
        parsed = urllib.parse.urlparse(neon_url)
        cfg = {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "dbname": parsed.path.lstrip("/"),
            "user": parsed.username or "postgres",
            "password": parsed.password or "",
            "sslmode": "require",
        }
        if parsed.hostname:
            resolved_ip = _resolve_neon_host(parsed.hostname)
            if resolved_ip:
                cfg["hostaddr"] = resolved_ip
        return cfg

    return {
        "host":     _get_local_param("DB_HOST", "localhost"),
        "port":     int(_get_local_param("DB_PORT", "5433")),
        "dbname":   _get_local_param("DB_NAME", "smartstock"),
        "user":     _get_local_param("DB_USER", "postgres"),
        "password": _get_local_param("DB_PASSWORD", ""),
    }


def get_engine():
    """Return a SQLAlchemy engine using Streamlit Secrets, .env credentials, or NEON_DATABASE_URL."""
    neon_url = _get_neon_url()
    if neon_url:
        url = neon_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        if "sslmode=" not in url:
            delimiter = "&" if "?" in url else "?"
            url = f"{url}{delimiter}sslmode=require"

        parsed = urllib.parse.urlparse(url)
        connect_args = {}
        if parsed.hostname:
            resolved_ip = _resolve_neon_host(parsed.hostname)
            if resolved_ip:
                connect_args["hostaddr"] = resolved_ip

        return create_engine(
            url,
            connect_args=connect_args,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )

    cfg = _get_cfg()
    if not cfg["password"]:
        raise RuntimeError(
            "Neither NEON_DATABASE_URL nor DB_PASSWORD is configured. "
            "Please configure your .env file or Streamlit Secrets."
        )

    url = (
        f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['dbname']}"
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )


def get_psycopg2_config() -> dict:
    """Return a psycopg2-compatible connection dict using active configuration."""
    return _get_cfg()
