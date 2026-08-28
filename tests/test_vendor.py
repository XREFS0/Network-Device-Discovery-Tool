import unittest
from pathlib import Path
from unittest.mock import patch
from app.services.vendor import VendorService

class TestVendor(unittest.TestCase):
    def test_normalize_oui(self) -> None:
        """Test normalization of MAC addresses to 6 hex characters."""
        self.assertEqual(VendorService.normalize_oui("00:11:22:33:44:55"), "001122")
        self.assertEqual(VendorService.normalize_oui("AA-BB-CC-DD-EE-FF"), "AABBCC")
        self.assertEqual(VendorService.normalize_oui("1234.5678.90ab"), "123456")
        self.assertEqual(VendorService.normalize_oui("aabbcc"), "AABBCC")

    def test_lookup_vendor(self) -> None:
        """Test looking up vendors from simulated database."""
        service = VendorService()
        
        # Test default/simulated loaded records
        # "00000C" is Cisco Systems in our data/oui.csv
        vendor = service.lookup_vendor("00:00:0C:11:22:33")
        self.assertEqual(vendor, "Cisco Systems")
        
        # Test unknown MAC
        unknown = service.lookup_vendor("FF:FF:FF:FF:FF:FF")
        self.assertEqual(unknown, "Unknown")

        # Test invalid MAC formats
        invalid = service.lookup_vendor("invalid_mac")
        self.assertEqual(invalid, "Unknown")
        
        # Test None/empty
        self.assertEqual(service.lookup_vendor(""), "Unknown")

if __name__ == "__main__":
    unittest.main()
