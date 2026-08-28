from enum import Enum

class DiscoveryMethod(Enum):
    AUTO = "Auto"
    ARP = "ARP"
    ICMP = "ICMP"
    TCP = "TCP"

class DeviceStatus(Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"
    UNKNOWN = "Unknown"
