import ipaddress
import logging
import psutil
from typing import List, Optional
from app.core.models import NetworkInterfaceInfo

logger = logging.getLogger(__name__)

class InterfaceDetector:
    @staticmethod
    def get_interfaces() -> List[NetworkInterfaceInfo]:
        """Detect and return available network interfaces with IPs, netmasks, and MACs using psutil."""
        interfaces = []
        try:
            if_addrs = psutil.net_if_addrs()
            for iface_name, addrs in if_addrs.items():
                ip = None
                netmask = None
                mac = None
                
                for addr in addrs:
                    if addr.family == 2:  # AF_INET
                        ip = addr.address
                        netmask = addr.netmask
                    elif addr.family == -1 or (hasattr(psutil, 'AF_LINK') and addr.family == psutil.AF_LINK):
                        mac = addr.address

                if not ip or ip == "127.0.0.1" or ip.startswith("169.254"):
                    continue

                if mac:
                    mac = mac.replace("-", ":").lower()
                
                network_range = None
                if ip and netmask:
                    try:
                        network_range = str(ipaddress.IPv4Interface(f"{ip}/{netmask}").network)
                    except ValueError:
                        pass
                
                interfaces.append(
                    NetworkInterfaceInfo(
                        name=iface_name,
                        ip_address=ip,
                        netmask=netmask,
                        network_range=network_range,
                        mac_address=mac
                    )
                )
        except Exception as e:
            logger.error(f"Error enumerating interfaces with psutil: {e}")
            
        return interfaces

    @staticmethod
    def get_default_interface() -> Optional[NetworkInterfaceInfo]:
        """Attempt to find the default active interface."""
        ifaces = InterfaceDetector.get_interfaces()
        if not ifaces:
            return None
        
        for iface in ifaces:
            if iface.ip_address and iface.mac_address and iface.network_range:
                return iface
        
        return ifaces[0]
