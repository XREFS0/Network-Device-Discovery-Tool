import time
import logging
from typing import List, Optional
import scapy.all as scapy
from app.core.models import Device
from app.core.constants import DiscoveryMethod, DeviceStatus

logger = logging.getLogger(__name__)

class ArpScanner:
    @staticmethod
    def scan(network_range: str, interface_name: Optional[str] = None, timeout: float = 1.0) -> List[Device]:
        """Perform Layer 2 ARP discovery on the specified subnet."""
        devices: List[Device] = []
        try:
            packet = scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=network_range)
            logger.info(f"Starting ARP scan on range: {network_range} via interface: {interface_name}")
            
            srp_kwargs = {"timeout": timeout, "verbose": 0}
            if interface_name:
                srp_kwargs["iface"] = interface_name
                
            ans, _ = scapy.srp(packet, **srp_kwargs)
            
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            for snd, rcv in ans:
                rtt = None
                if hasattr(rcv, 'time') and hasattr(snd, 'time'):
                    rtt = float(rcv.time - snd.time) * 1000.0
                    
                devices.append(
                    Device(
                        ip_address=rcv.psrc,
                        mac_address=rcv.hwsrc,
                        status=DeviceStatus.ONLINE,
                        method=DiscoveryMethod.ARP,
                        response_time_ms=round(rtt, 2) if rtt is not None else None,
                        first_seen=current_time,
                        last_seen=current_time
                    )
                )
            
            logger.info(f"ARP scan completed. Discovered {len(devices)} devices.")
        except PermissionError as e:
            logger.error("Permission error during ARP scan. Administrator/root privileges are required.")
            raise PermissionError("Administrative privileges are required for raw socket operations (ARP scan).") from e
        except Exception as e:
            logger.error(f"Error during ARP scan: {e}")
            raise e
            
        return devices
