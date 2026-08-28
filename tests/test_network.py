import ipaddress
import unittest
from unittest.mock import patch, MagicMock
from app.core.models import NetworkInterfaceInfo
from app.discovery.interface import InterfaceDetector

class TestNetwork(unittest.TestCase):
    def test_ip_subnet_calculation(self) -> None:
        """Test standard IPv4 subnet calculations."""
        ip = "192.168.1.50"
        netmask = "255.255.255.0"
        network_range = str(ipaddress.IPv4Interface(f"{ip}/{netmask}").network)
        self.assertEqual(network_range, "192.168.1.0/24")

    @patch("app.discovery.interface.psutil.net_if_addrs")
    def test_get_interfaces(self, mock_net_if_addrs) -> None:
        """Test interface detection with mocked psutil net_if_addrs."""
        # snicaddr structures are named tuples: (family, address, netmask, broadcast, ptp)
        addr_ip = MagicMock()
        addr_ip.family = 2  # AF_INET
        addr_ip.address = "192.168.1.15"
        addr_ip.netmask = "255.255.255.0"
        
        addr_link = MagicMock()
        addr_link.family = -1  # AF_LINK (Windows)
        addr_link.address = "00-11-22-33-44-55"
        addr_link.netmask = None
        
        mock_net_if_addrs.return_value = {
            "Ethernet 1": [addr_ip, addr_link]
        }
        
        ifaces = InterfaceDetector.get_interfaces()
        
        self.assertEqual(len(ifaces), 1)
        self.assertEqual(ifaces[0].name, "Ethernet 1")
        self.assertEqual(ifaces[0].ip_address, "192.168.1.15")
        self.assertEqual(ifaces[0].network_range, "192.168.1.0/24")
        self.assertEqual(ifaces[0].mac_address, "00:11:22:33:44:55")

if __name__ == "__main__":
    unittest.main()
