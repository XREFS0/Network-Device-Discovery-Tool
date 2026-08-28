import csv
import json
import logging
from pathlib import Path
from typing import List
from app.core.models import Device

logger = logging.getLogger(__name__)

class ExportService:
    @staticmethod
    def to_csv(devices: List[Device], filepath: Path) -> None:
        """Export device list to a CSV file."""
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header row
                writer.writerow([
                    "IP Address",
                    "MAC Address",
                    "Hostname",
                    "Vendor",
                    "Status",
                    "Discovery Method",
                    "Response Time (ms)",
                    "First Seen",
                    "Last Seen"
                ])
                
                for dev in devices:
                    writer.writerow([
                        dev.ip_address,
                        dev.mac_address,
                        dev.hostname,
                        dev.vendor,
                        dev.status.value,
                        dev.method.value,
                        dev.response_time_ms if dev.response_time_ms is not None else "",
                        dev.first_seen,
                        dev.last_seen
                    ])
            logger.info(f"Successfully exported {len(devices)} devices to CSV: {filepath}")
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            raise

    @staticmethod
    def to_json(devices: List[Device], filepath: Path) -> None:
        """Export device list to a JSON file."""
        try:
            data = [dev.to_dict() for dev in devices]
            with open(filepath, mode="w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Successfully exported {len(devices)} devices to JSON: {filepath}")
        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            raise
