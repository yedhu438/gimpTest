"""
db.py — Central database connection for Varsany Print Automation
================================================================
All scripts import get_connection() from here instead of building
their own connection strings. Credentials come from .env so you
only ever need to update one file when the VPS details change.

Usage:
    from db import get_connection

    conn = get_connection()
    cur  = conn.cursor()
    ...
    conn.close()
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass  # python-dotenv not installed — relies on environment variables already set

import pyodbc

# ── Read credentials from environment (set in .env) ──────────────────────────
_server = os.environ.get("DB_SERVER", r"81.0.219.26")
_name   = os.environ.get("DB_NAME",   "dbAmazonCustomOrders")
_uid    = os.environ.get("DB_UID",    "")
_pwd    = os.environ.get("DB_PWD",    "")

# ── Build connection string ───────────────────────────────────────────────────
# SQL Server auth (UID + PWD) when credentials are provided (live VPS).
# Falls back to Windows auth (Trusted_Connection) for local SQLEXPRESS.
if _uid and _pwd:
    _CONN_STR = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={_server};DATABASE={_name};"
        f"UID={_uid};PWD={_pwd};"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )
else:
    _CONN_STR = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={_server};DATABASE={_name};"
        "Trusted_Connection=yes;TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

# Fallback to the older "SQL Server" driver if ODBC 17 is not installed
def _build_conn_str(driver: str) -> str:
    if _uid and _pwd:
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={_server};DATABASE={_name};"
            f"UID={_uid};PWD={_pwd};"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={_server};DATABASE={_name};"
        "Trusted_Connection=yes;TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )


def get_connection(timeout: int = 30) -> pyodbc.Connection:
    """Return an open pyodbc connection to the database.

    Tries ODBC Driver 17 first, then falls back to the legacy
    'SQL Server' driver so the code works on machines that only
    have the older driver installed.
    """
    drivers_to_try = ["ODBC Driver 17 for SQL Server", "SQL Server"]
    last_err = None
    for driver in drivers_to_try:
        cs = _build_conn_str(driver)
        try:
            return pyodbc.connect(cs, timeout=timeout)
        except pyodbc.Error as exc:
            last_err = exc
            continue

    # Both drivers failed — give a clear error message
    print(
        f"\n[db.py] ERROR: Cannot connect to SQL Server at {_server}.\n"
        f"  Database : {_name}\n"
        f"  User     : {_uid or '(Windows auth)'}\n"
        f"  Reason   : {last_err}\n\n"
        "  Check that:\n"
        "    1. Your Windows VPS is reachable (ping 81.0.219.26)\n"
        "    2. SQL Server port 1433 is open on the VPS firewall\n"
        "    3. DB_UID / DB_PWD in .env are correct\n"
        "    4. An ODBC driver is installed: "
        "'ODBC Driver 17 for SQL Server' or 'SQL Server'\n",
        file=sys.stderr,
    )
    raise last_err


# ── Quick connectivity test ───────────────────────────────────────────────────
def test_connection() -> bool:
    """Return True if the database is reachable, False otherwise."""
    try:
        conn = get_connection(timeout=10)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


# ── CLI self-test: python db.py ───────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Connecting to {_server} / {_name} …")
    try:
        conn = get_connection()
        row = conn.execute("SELECT @@VERSION").fetchone()
        print("Connected successfully.")
        print("SQL Server version:", row[0].split("\n")[0])
        conn.close()
    except Exception as exc:
        print(f"Connection failed: {exc}")
        sys.exit(1)
