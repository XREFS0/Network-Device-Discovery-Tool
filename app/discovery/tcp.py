import time
import socket
import logging
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from app.core.models import Device
from app.core.constants import DiscoveryMethod, DeviceStatus

logger = logging.getLogger(__name__)

class TcpScanner:
    COMMON_PORTS = [80, 443, 22, 135, 445]

    @staticmethod
    def check_host(ip: str, timeout: float = 0.5) -> Optional[Device]:
        """Verify host activity by checking socket responses on standard utility ports."""
        start_time = time.time()
        for port in TcpScanner.COMMON_PORTS:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            try:
                result = s.connect_ex((ip, port))
                is_alive = False
                if result == 0:
                    is_alive = True
                else:
                    # Windows WSAECONNREFUSED (10061) or Linux ECONNREFUSED (111) indicates host is active
                    if result in (10061, 111):
                        is_alive = True
                
                if is_alive:
                    elapsed = (time.time() - start_time) * 1000.0
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    return Device(
                        ip_address=ip,
                        mac_address="Unknown",
                        status=DeviceStatus.ONLINE,
                        method=DiscoveryMethod.TCP,
                        response_time_ms=round(elapsed, 2),
                        first_seen=current_time,
                        last_seen=current_time
                    )
            except Exception:
                pass
            finally:
                s.close()
        return None

    @staticmethod
    def scan(network_range: str, timeout: float = 0.5, max_workers: int = 50) -> List[Device]:
        """Perform concurrent port checks on a subnet using thread pools."""
        devices: List[Device] = []
        try:
            network = ipaddress.ip_network(network_range, strict=False)
            hosts = [str(ip) for ip in network.hosts()]
            
            if len(hosts) > 512:
                logger.warning(f"Subnet {network_range} has {len(hosts)} hosts. Limiting scan to first 512 hosts.")
                hosts = hosts[:512]
                
            if not hosts:
                return []

            logger.info(f"Starting TCP scan on {len(hosts)} hosts using {max_workers} workers...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(TcpScanner.check_host, ip, timeout): ip for ip in hosts}
                for future in as_completed(futures):
                    try:
                        device = future.result()
                        if device:
                            devices.append(device)
                    except Exception as e:
                        ip = futures[future]
                        logger.debug(f"Error checking host {ip} via TCP: {e}")
                        
            logger.info(f"TCP scan completed. Discovered {len(devices)} devices.")
        except Exception as e:
            logger.error(f"Error during TCP scan: {e}")
            
        return devices
