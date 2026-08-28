import sqlite3
import logging
from pathlib import Path
from typing import Generator
from app.core.config import Config

logger = logging.getLogger(__name__)

def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection with foreign keys enabled."""
    Config.ensure_dirs()
    try:
        conn = sqlite3.connect(str(Config.DB_PATH))
        conn.row_factory = sqlite3.Row
        # Enable foreign key support in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def initialize_database() -> None:
    """Initialize database tables using the schema.sql file."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        return

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        conn = get_db_connection()
        try:
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()
        logger.info("Database initialized successfully.")
    except (sqlite3.Error, OSError) as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
