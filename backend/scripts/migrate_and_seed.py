#!/usr/bin/env python3
"""
Production migration + optional demo seed.

Usage:
    # Run migrations only
    python -m scripts.migrate_and_seed

    # Run migrations + seed demo data
    python -m scripts.migrate_and_seed --seed

Requires DATABASE_URL to be set (reads from .env or environment).
"""

import argparse
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def run_migrations() -> bool:
    """Run alembic upgrade head."""
    print("=" * 50)
    print("  Running Alembic migrations …")
    print("=" * 50)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(BACKEND_DIR),
    )
    if result.returncode != 0:
        print("ERROR: Alembic migration failed!")
        return False
    print("Migrations applied successfully.\n")
    return True


def run_seed() -> bool:
    """Run the production seed (seeds into real DATABASE_URL)."""
    print("=" * 50)
    print("  Seeding demo data (production) …")
    print("=" * 50)
    result = subprocess.run(
        [sys.executable, "-m", "scripts.seed_production"],
        cwd=str(BACKEND_DIR),
    )
    if result.returncode != 0:
        print("ERROR: Seed script failed!")
        return False
    print("Production seed completed.\n")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="PassportAI DB migration + seed")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Also run demo seed after migrations",
    )
    args = parser.parse_args()

    if not run_migrations():
        sys.exit(1)

    if args.seed:
        if not run_seed():
            sys.exit(1)

    print("Done!")


if __name__ == "__main__":
    main()
