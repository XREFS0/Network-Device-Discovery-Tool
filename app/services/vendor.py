import csv
import logging
from typing import Dict
from app.core.config import Config

logger = logging.getLogger(__name__)

class VendorService:
    _instance = None
    _oui_db: Dict[str, str] = {}
    _loaded = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VendorService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if not self._loaded:
            self._load_oui_db()

    def _load_oui_db(self) -> None:
        """Load the OUI database from the CSV file."""
        oui_path = Config.OUI_PATH
        if not oui_path.exists():
            logger.warning(f"OUI file not found at {oui_path}. Vendor lookups will return 'Unknown'.")
            self._oui_db = {}
            self._loaded = True
            return

        try:
            with open(oui_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)  # Skip header
                
                db = {}
                for row in reader:
                    if len(row) >= 2:
                        oui = self.normalize_oui(row[0])
                        vendor = row[1].strip()
                        if oui and vendor:
                            db[oui] = vendor
                
                self._oui_db = db
                self._loaded = True
                logger.info(f"Loaded {len(self._oui_db)} OUI records.")
        except Exception as e:
            logger.error(f"Failed to load OUI database: {e}")
            self._oui_db = {}
            self._loaded = True

    @staticmethod
    def normalize_oui(mac_or_oui: str) -> str:
        """Extract the first 3 bytes (6 hex characters) from a MAC and normalize it to uppercase clean hex."""
        clean = "".join(c for c in mac_or_oui if c.isalnum()).upper()
        return clean[:6]

    def lookup_vendor(self, mac_address: str) -> str:
        """Look up the vendor name for a given MAC address."""
        if not mac_address or mac_address.lower() == "unknown":
            return "Unknown"
        
        normalized = self.normalize_oui(mac_address)
        if len(normalized) < 6:
            return "Unknown"
            
        return self._oui_db.get(normalized, "Unknown")
