from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from app.core.constants import DiscoveryMethod, DeviceStatus

@dataclass
class NetworkInterfaceInfo:
    name: str
    ip_address: Optional[str] = None
    netmask: Optional[str] = None
    network_range: Optional[str] = None
    mac_address: Optional[str] = None

@dataclass
class Device:
    ip_address: str
    mac_address: str = "Unknown"
    hostname: str = "Unknown"
    vendor: str = "Unknown"
    status: DeviceStatus = DeviceStatus.ONLINE
    method: DiscoveryMethod = DiscoveryMethod.AUTO
    response_time_ms: Optional[float] = None
    first_seen: str = ""
    last_seen: str = ""
    discovery_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "status": self.status.value,
            "method": self.method.value,
            "response_time_ms": self.response_time_ms,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "discovery_count": self.discovery_count
        }

@dataclass
class ScanInfo:
    id: Optional[int] = None
    start_time: str = ""
    end_time: Optional[str] = None
    network_range: str = ""
    interface_name: str = ""
    discovery_method: DiscoveryMethod = DiscoveryMethod.AUTO
    device_count: int = 0
