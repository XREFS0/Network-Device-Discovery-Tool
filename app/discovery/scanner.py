import logging
from typing import List, Optional, Callable
from app.core.models import Device
from app.core.constants import DiscoveryMethod
from app.discovery.arp import ArpScanner
from app.discovery.icmp import IcmpScanner
from app.discovery.tcp import TcpScanner

logger = logging.getLogger(__name__)

class NetworkScanner:
    def __init__(self, is_cancelled_cb: Optional[Callable[[], bool]] = None) -> None:
        """
        Initialize scanner.
        is_cancelled_cb: A callback function that returns True if the scan should cancel.
        """
        self.is_cancelled_cb = is_cancelled_cb or (lambda: False)

    def scan(
        self,
        network_range: str,
        method: DiscoveryMethod = DiscoveryMethod.AUTO,
        interface_name: Optional[str] = None,
        timeout: float = 1.0,
        max_workers: int = 4
    ) -> List[Device]:
        """Orchestrate scanning based on selected method with fallbacks."""
        if self.is_cancelled_cb():
            logger.info("Scan cancelled before starting.")
            return []

        devices: List[Device] = []
        
        # Determine actual scan method if AUTO
        if method == DiscoveryMethod.AUTO:
            logger.info("Auto method selected. Attempting ARP scan first.")
            try:
                devices = ArpScanner.scan(network_range, interface_name, timeout)
                # If ARP scan worked and found hosts, or finished without error
                return devices
            except PermissionError:
                logger.warning("ARP scan failed due to permissions. Falling back to TCP scan.")
                if self.is_cancelled_cb():
                    return []
                return TcpScanner.scan(network_range, timeout, max_workers=max_workers * 10) # Give it more workers for TCP
            except Exception as e:
                logger.warning(f"ARP scan failed: {e}. Falling back to TCP scan.")
                if self.is_cancelled_cb():
                    return []
                return TcpScanner.scan(network_range, timeout, max_workers=max_workers * 10)
                
        elif method == DiscoveryMethod.ARP:
            # Explicit ARP scan (requires admin)
            return ArpScanner.scan(network_range, interface_name, timeout)
            
        elif method == DiscoveryMethod.ICMP:
            # Explicit ICMP scan (requires admin in Scapy)
            try:
                return IcmpScanner.scan(network_range, timeout)
            except PermissionError:
                logger.error("ICMP scan failed due to permissions.")
                raise PermissionError("Administrative privileges are required for ICMP raw socket scanning.")
                
        elif method == DiscoveryMethod.TCP:
            # Explicit TCP scan (non-admin friendly)
            # We scale workers up because TCP connect is blocking per connection.
            # default max_workers is 4, but we can scale it to say 50 for TCP
            tcp_workers = max_workers * 10 if max_workers < 15 else max_workers
            return TcpScanner.scan(network_range, timeout, max_workers=tcp_workers)

        return devices
