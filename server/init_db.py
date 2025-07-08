"""Database initialization utility for AI DJ."""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent))

from routes.settings import init_db, get_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_environment() -> None:
    """Load environment variables from a .env file if present."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        load_dotenv(env_path)

def test_connection():
    """Test database connectivity."""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        logger.info("Database connection successful.")
        return True
    except Exception as e:
        logger.exception("Database connection failed: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser(description="Initialize or test the AI DJ database")
    parser.add_argument("--test", action="store_true", help="Only test the database connection")
    args = parser.parse_args()

    load_environment()

    if args.test:
        test_connection()
        return

    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.exception("Database initialization failed: %s", e)

if __name__ == "__main__":
    main()

