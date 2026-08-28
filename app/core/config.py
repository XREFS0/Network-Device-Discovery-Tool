from pathlib import Path
import os

class Config:
    # Directories
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    
    # SQLite Database path
    DB_PATH = DATA_DIR / "history.db"
    
    # OUI database path
    OUI_PATH = DATA_DIR / "oui.csv"
    
    # App Logging
    LOG_DIR = BASE_DIR / "logs"
    LOG_FILE = LOG_DIR / "app.log"
    
    # Default scan settings
    DEFAULT_TIMEOUT = 1.0
    DEFAULT_WORKERS = 4
    DEFAULT_RESOLVE_HOSTNAMES = True
    DEFAULT_LOOKUP_VENDORS = True

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create necessary directories if they do not exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
