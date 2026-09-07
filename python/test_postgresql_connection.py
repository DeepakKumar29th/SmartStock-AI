from pathlib import Path
import os

import psycopg2
from dotenv import load_dotenv


# ============================================================
# SMARTSTOCK AI
# STEP 3.1 - POSTGRESQL CONNECTION TEST
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


print("=" * 70)
print("SMARTSTOCK AI - STEP 3.1")
print("PostgreSQL Connection Test")
print("=" * 70)

print("\nConnection configuration:")
print(f"Host     : {DB_HOST}")
print(f"Port     : {DB_PORT}")
print(f"Database : {DB_NAME}")
print(f"User     : {DB_USER}")
print("Password : [HIDDEN]")


required_values = {
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
}

missing = [
    key
    for key, value in required_values.items()
    if not value
]

if missing:

    print("\nERROR")
    print("Missing environment variables:")

    for key in missing:
        print(f"- {key}")

    raise SystemExit(1)


try:

    connection = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=10,
    )

    cursor = connection.cursor()

    cursor.execute(
        "SELECT current_database(), current_user, version();"
    )

    database_name, current_user, version = cursor.fetchone()

    print("\n" + "=" * 70)
    print("CONNECTION SUCCESSFUL")
    print("=" * 70)

    print(f"Database : {database_name}")
    print(f"User     : {current_user}")
    print(f"Server   : {version}")

    cursor.close()
    connection.close()

    print("\nConnection closed successfully.")

except Exception as error:

    print("\n" + "=" * 70)
    print("CONNECTION FAILED")
    print("=" * 70)

    print(f"\nError: {error}")

    raise SystemExit(1)