import socket
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class HostnameResolver:
    def __init__(self, timeout: float = 1.0) -> None:
        self.timeout = timeout
        self._cache: Dict[str, str] = {}

    def resolve(self, ip_address: str) -> str:
        """Resolve IP address to hostname with cache and timeout fallback."""
        if ip_address in self._cache:
            return self._cache[ip_address]

        # Save previous default timeout
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.timeout)
        
        hostname = "Unknown"
        try:
            # socket.gethostbyaddr returns (hostname, aliaslist, ipaddrlist)
            resolved = socket.gethostbyaddr(ip_address)
            if resolved and resolved[0]:
                hostname = resolved[0]
        except (socket.herror, socket.timeout, socket.gaierror):
            # Normal DNS resolution failures, expected for many LAN IPs
            pass
        except Exception as e:
            logger.debug(f"Unexpected error resolving hostname for {ip_address}: {e}")
        finally:
            # Restore previous default timeout
            socket.setdefaulttimeout(old_timeout)
            
        self._cache[ip_address] = hostname
        return hostname
