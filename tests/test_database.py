import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.core.config import Config
from app.core.models import ScanInfo, Device
from app.core.constants import DiscoveryMethod, DeviceStatus

class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        # Create temporary directory for test database
        self.temp_dir = TemporaryDirectory()
        self.test_db_path = Path(self.temp_dir.name) / "test_history.db"
        
        # Patch Config.DB_PATH to use the test db file
        self.db_path_patcher = patch.object(Config, "DB_PATH", self.test_db_path)
        self.db_path_patcher.start()
        
        # Initialize database schema
        from app.database.connection import initialize_database
        initialize_database()
        
        from app.database.repository import ScanRepository
        self.repo = ScanRepository()

    def tearDown(self) -> None:
        self.db_path_patcher.stop()
        self.temp_dir.cleanup()

    def test_insert_and_retrieve_scan(self) -> None:
        """Test inserting a scan session and retrieving it."""
        scan = ScanInfo(
            start_time="2026-08-28 22:00:00",
            network_range="192.168.1.0/24",
            interface_name="eth0",
            discovery_method=DiscoveryMethod.ARP
        )
        
        scan_id = self.repo.insert_scan(scan)
        self.assertIsNotNone(scan_id)
        
        # Update completion details
        self.repo.update_scan_completion(scan_id, "2026-08-28 22:01:00", 2)
        
        # Fetch scans
        scans = self.repo.get_all_scans()
        self.assertEqual(len(scans), 1)
        self.assertEqual(scans[0].id, scan_id)
        self.assertEqual(scans[0].device_count, 2)
        self.assertEqual(scans[0].end_time, "2026-08-28 22:01:00")

    def test_insert_and_retrieve_device(self) -> None:
        """Test inserting devices under a scan session."""
        scan = ScanInfo(
            start_time="2026-08-28 22:00:00",
            network_range="192.168.1.0/24",
            interface_name="eth0",
            discovery_method=DiscoveryMethod.ARP
        )
        scan_id = self.repo.insert_scan(scan)
        
        device1 = Device(
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55",
            hostname="test-host",
            vendor="Intel",
            status=DeviceStatus.ONLINE,
            method=DiscoveryMethod.ARP,
            response_time_ms=1.5,
            first_seen="2026-08-28 22:00:00",
            last_seen="2026-08-28 22:00:00",
            discovery_count=1
        )
        
        self.repo.insert_device(scan_id, device1)
        
        # Retrieve devices
        devices = self.repo.get_scan_devices(scan_id)
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0].ip_address, "192.168.1.100")
        self.assertEqual(devices[0].mac_address, "00:11:22:33:44:55")
        
        # Test historical summary
        history = self.repo.get_device_history_summary("192.168.1.100", "00:11:22:33:44:55")
        self.assertEqual(history["discovery_count"], 1)

if __name__ == "__main__":
    unittest.main()
