import json
import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.core.models import Device
from app.core.constants import DiscoveryMethod, DeviceStatus
from app.services.export import ExportService

class TestExport(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.export_dir = Path(self.temp_dir.name)
        
        self.devices = [
            Device(
                ip_address="192.168.1.10",
                mac_address="00:11:22:33:44:55",
                hostname="host-a",
                vendor="Intel",
                status=DeviceStatus.ONLINE,
                method=DiscoveryMethod.ARP,
                response_time_ms=2.4,
                first_seen="2026-08-28 22:00:00",
                last_seen="2026-08-28 22:00:00",
                discovery_count=1
            ),
            Device(
                ip_address="192.168.1.20",
                mac_address="AA:BB:CC:DD:EE:FF",
                hostname="host-b",
                vendor="Apple",
                status=DeviceStatus.ONLINE,
                method=DiscoveryMethod.TCP,
                response_time_ms=10.5,
                first_seen="2026-08-28 22:00:00",
                last_seen="2026-08-28 22:00:00",
                discovery_count=2
            )
        ]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_csv_export(self) -> None:
        """Verify device list is correctly serialized to CSV format."""
        csv_file = self.export_dir / "export.csv"
        ExportService.to_csv(self.devices, csv_file)
        
        self.assertTrue(csv_file.exists())
        
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            
            # Check headers
            self.assertEqual(reader[0][0], "IP Address")
            self.assertEqual(reader[0][1], "MAC Address")
            
            # Check row count
            self.assertEqual(len(reader), 3) # 1 header + 2 rows
            
            # Check values
            self.assertEqual(reader[1][0], "192.168.1.10")
            self.assertEqual(reader[1][2], "host-a")
            self.assertEqual(reader[2][0], "192.168.1.20")
            self.assertEqual(reader[2][4], "Online")

    def test_json_export(self) -> None:
        """Verify device list is correctly serialized to JSON format."""
        json_file = self.export_dir / "export.json"
        ExportService.to_json(self.devices, json_file)
        
        self.assertTrue(json_file.exists())
        
        with open(json_file, mode="r", encoding="utf-8") as f:
            data = json.load(f)
            
            self.assertEqual(len(data), 2)
            self.assertEqual(data[0]["ip_address"], "192.168.1.10")
            self.assertEqual(data[0]["hostname"], "host-a")
            self.assertEqual(data[0]["status"], "Online")
            self.assertEqual(data[1]["ip_address"], "192.168.1.20")
            self.assertEqual(data[1]["vendor"], "Apple")

if __name__ == "__main__":
    unittest.main()
