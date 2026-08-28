import time
import logging
from typing import List, Dict, Any
from app.core.models import ScanInfo, Device
from app.core.constants import DiscoveryMethod
from app.database.repository import ScanRepository

logger = logging.getLogger(__name__)

class ScanService:
    def __init__(self) -> None:
        self.repository = ScanRepository()

    def start_scan_session(
        self,
        network_range: str,
        interface_name: str,
        method: DiscoveryMethod
    ) -> int:
        """Create a new scan entry in the database and return its session ID."""
        start_time = time.strftime("%Y-%m-%d %H:%M:%S")
        scan_info = ScanInfo(
            start_time=start_time,
            network_range=network_range,
            interface_name=interface_name,
            discovery_method=method
        )
        scan_id = self.repository.insert_scan(scan_info)
        logger.info(f"Started scan session {scan_id} in database.")
        return scan_id

    def complete_scan_session(self, scan_id: int, devices: List[Device]) -> None:
        """Save all discovered devices to the database and update scan completion status."""
        end_time = time.strftime("%Y-%m-%d %H:%M:%S")
        device_count = len(devices)
        
        # 1. Update Scan completion details
        self.repository.update_scan_completion(scan_id, end_time, device_count)
        
        # 2. Insert all devices
        for device in devices:
            # Query historical occurrences to compute discovery_count and first_seen
            history = self.repository.get_device_history_summary(device.ip_address, device.mac_address)
            
            if history["discovery_count"] > 0:
                # Device has been seen before
                device.first_seen = history["first_seen"]
                device.discovery_count = history["discovery_count"] + 1
            else:
                # Brand new device
                # Device first_seen is already set to current time in scanner, which is correct
                device.discovery_count = 1
                
            self.repository.insert_device(scan_id, device)
            
        logger.info(f"Completed scan session {scan_id} with {device_count} devices saved.")

    def get_history(self) -> List[ScanInfo]:
        """Fetch all previous scans."""
        return self.repository.get_all_scans()

    def get_scan_results(self, scan_id: int) -> List[Device]:
        """Fetch discovered devices for a past scan."""
        return self.repository.get_scan_devices(scan_id)

    def delete_scan(self, scan_id: int) -> None:
        """Delete a single scan session and its devices."""
        self.repository.delete_scan(scan_id)
        logger.info(f"Deleted scan session {scan_id} from database.")

    def clear_all_history(self) -> None:
        """Clear the entire database scan and device history."""
        self.repository.clear_all_history()
        logger.info("Cleared all database history.")

    def get_device_history(self, ip_address: str, mac_address: str) -> Dict[str, Any]:
        """Retrieve aggregated historical stats for a device (first seen, last seen, count)."""
        return self.repository.get_device_history_summary(ip_address, mac_address)
