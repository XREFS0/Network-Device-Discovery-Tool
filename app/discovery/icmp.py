import time
import logging
import ipaddress
from typing import List, Optional
import scapy.all as scapy
from app.core.models import Device
from app.core.constants import DiscoveryMethod, DeviceStatus

logger = logging.getLogger(__name__)

class IcmpScanner:
    @staticmethod
    def scan(network_range: str, timeout: float = 1.0) -> List[Device]:
        """Perform Layer 3 ICMP ping discovery on the specified subnet."""
        devices: List[Device] = []
        try:
            network = ipaddress.ip_network(network_range, strict=False)
            hosts = [str(ip) for ip in network.hosts()]
            
            # Prevent scanning excessively large networks to protect system memory
            if len(hosts) > 512:
                logger.warning(f"Subnet {network_range} has {len(hosts)} hosts. Limiting scan to first 512 hosts.")
                hosts = hosts[:512]
                
            if not hosts:
                return []

            logger.info(f"Starting ICMP scan on {len(hosts)} hosts...")
            packet = scapy.IP(dst=hosts) / scapy.ICMP()
            ans, _ = scapy.sr(packet, timeout=timeout, verbose=0)
            
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            for snd, rcv in ans:
                rtt = None
                if hasattr(rcv, 'time') and hasattr(snd, 'time'):
                    rtt = float(rcv.time - snd.time) * 1000.0
                
                devices.append(
                    Device(
                        ip_address=rcv.src,
                        mac_address="Unknown",
                        status=DeviceStatus.ONLINE,
                        method=DiscoveryMethod.ICMP,
                        response_time_ms=round(rtt, 2) if rtt is not None else None,
                        first_seen=current_time,
                        last_seen=current_time
                    )
                )
                
            logger.info(f"ICMP scan completed. Discovered {len(devices)} devices.")
        except PermissionError as e:
            logger.error("Permission error during ICMP scan. Administrator/root privileges are required.")
            raise PermissionError("Administrative privileges are required for raw socket operations (ICMP scan).") from e
        except Exception as e:
            logger.error(f"Error during ICMP scan: {e}")
            raise e
            
        return devices
