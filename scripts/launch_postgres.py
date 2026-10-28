"""
BrandShield AI - One-Command Automated PostgreSQL Launcher.
Detects or initializes a dedicated PostgreSQL cluster, starts the engine,
and ensures the application database exists.
"""

import asyncio
import os
import socket
import subprocess
import sys
import time
import asyncpg


def is_port_open(host: str, port: int) -> bool:
    """Checks if a network port is accepting connections."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        res = s.connect_ex((host, port))
        return res == 0
    finally:
        s.close()


def find_postgres_binary_dir() -> str:
    """Locates postgres binary directory across standard Windows locations."""
    candidates = [
        r"C:\Program Files\PostgreSQL\18\bin",
        r"C:\Program Files\PostgreSQL\17\bin",
        r"C:\Program Files\PostgreSQL\16\bin",
        r"C:\Program Files\PostgreSQL\15\bin",
    ]
    for c in candidates:
        if os.path.exists(os.path.join(c, "postgres.exe")):
            return c
    return ""


async def ensure_database_exists(port: int, db_name: str = "brandshield_ai"):
    """Connects to default postgres database and creates target db if missing."""
    conn = await asyncpg.connect(user="postgres", host="localhost", port=port, database="postgres")
    try:
        dbs = [r["datname"] for r in await conn.fetch("SELECT datname FROM pg_database;")]
        if db_name not in dbs:
            await conn.execute(f'CREATE DATABASE "{db_name}";')
            print(f"[OK] Created database '{db_name}'.")
        else:
            print(f"[OK] Database '{db_name}' already exists.")
    finally:
        await conn.close()


def main():
    port = int(os.environ.get("POSTGRES_PORT", "5433"))
    db_name = os.environ.get("POSTGRES_DB", "brandshield_ai")

    print(f"Checking PostgreSQL availability on localhost:{port}...")
    if is_port_open("localhost", port):
        print(f"[OK] PostgreSQL is actively running on port {port}.")
        asyncio.run(ensure_database_exists(port, db_name))
        return

    # Check standard port 5432 as well
    if port != 5432 and is_port_open("localhost", 5432):
        print("Note: Port 5432 is in use by another service. Launching dedicated instance on port 5433.")

    pg_bin = find_postgres_binary_dir()
    if not pg_bin:
        print("[ERROR] Could not find PostgreSQL installation in Program Files. Please ensure PostgreSQL is installed.")
        sys.exit(1)

    pg_data = os.path.join(os.path.expanduser("~"), ".brandshield_pgdata")
    initdb = os.path.join(pg_bin, "initdb.exe")
    pg_ctl = os.path.join(pg_bin, "pg_ctl.exe")

    if not os.path.exists(pg_data):
        print(f"Initializing new PostgreSQL data directory at '{pg_data}'...")
        res = subprocess.run([initdb, "-D", pg_data, "-U", "postgres", "-A", "trust", "-E", "UTF8"], capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[ERROR] initdb failed: {res.stderr}")
            sys.exit(1)
        print("[OK] PostgreSQL cluster initialized.")

    print(f"Starting PostgreSQL server on port {port}...")
    log_file = os.path.join(pg_data, "server.log")
    res = subprocess.run([pg_ctl, "-D", pg_data, "-l", log_file, "-o", f"-p {port}", "start"], capture_output=True, text=True)

    # Wait for server readiness
    started = False
    for _ in range(15):
        time.sleep(1)
        if is_port_open("localhost", port):
            started = True
            break

    if not started:
        print(f"[ERROR] Failed to start PostgreSQL on port {port}. Log:")
        if os.path.exists(log_file):
            print(open(log_file).read()[-500:])
        sys.exit(1)

    print(f"[OK] PostgreSQL server successfully running on port {port}.")
    asyncio.run(ensure_database_exists(port, db_name))
    print("[SUCCESS] Dedicated BrandShield AI PostgreSQL instance is healthy and ready.")


if __name__ == "__main__":
    main()
