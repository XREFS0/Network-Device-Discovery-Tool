import time
import logging
from typing import List, Optional
from PySide6.QtCore import QThread, Signal
from app.core.models import Device
from app.core.constants import DiscoveryMethod, DeviceStatus
from app.discovery.scanner import NetworkScanner
from app.services.hostname import HostnameResolver
from app.services.vendor import VendorService

logger = logging.getLogger(__name__)

class ScanWorker(QThread):
    # Signals
    started_signal = Signal()
    progress_signal = Signal(int, str, int, int) # percent, status_text, processed, discovered
    device_discovered_signal = Signal(Device)
    finished_signal = Signal(list, float) # list of devices, elapsed time
    error_signal = Signal(str)

    def __init__(
        self,
        network_range: str,
        method: DiscoveryMethod,
        interface_name: Optional[str],
        timeout: float,
        workers: int,
        resolve_hostnames: bool,
        lookup_vendors: bool
    ) -> None:
        super().__init__()
        self.network_range = network_range
        self.method = method
        self.interface_name = interface_name
        self.timeout = timeout
        self.workers = workers
        self.resolve_hostnames = resolve_hostnames
        self.lookup_vendors = lookup_vendors
        
        self._is_cancelled = False
        self.vendor_service = VendorService()
        self.hostname_resolver = HostnameResolver()

    def cancel(self) -> None:
        """Request scan cancellation."""
        self._is_cancelled = True
        logger.info("Cancellation requested for background scan worker.")

    def is_cancelled(self) -> bool:
        return self._is_cancelled

    def run(self) -> None:
        """Run the scan thread."""
        self.started_signal.emit()
        start_time = time.time()
        
        try:
            self.progress_signal.emit(10, "Detecting hosts...", 0, 0)
            
            # 1. Discover hosts
            scanner = NetworkScanner(is_cancelled_cb=self.is_cancelled)
            discovered_devices = scanner.scan(
                network_range=self.network_range,
                method=self.method,
                interface_name=self.interface_name,
                timeout=self.timeout,
                max_workers=self.workers
            )
            
            if self._is_cancelled:
                self.progress_signal.emit(100, "Scan cancelled.", len(discovered_devices), len(discovered_devices))
                self.finished_signal.emit([], time.time() - start_time)
                return

            total_devices = len(discovered_devices)
            logger.info(f"Discovered {total_devices} active hosts. Starting enrichment phase.")
            
            enriched_devices: List[Device] = []
            
            # 2. Enrich hosts (Vendor Lookup & Hostname resolution)
            for idx, device in enumerate(discovered_devices):
                if self._is_cancelled:
                    break
                
                percent = int(10 + (idx / max(1, total_devices)) * 80)
                self.progress_signal.emit(
                    percent,
                    f"Enriching device {idx + 1}/{total_devices} ({device.ip_address})...",
                    idx,
                    len(enriched_devices)
                )
                
                # Vendor Lookup (fast, local)
                if self.lookup_vendors and device.mac_address:
                    device.vendor = self.vendor_service.lookup_vendor(device.mac_address)
                
                # Hostname Resolution (potentially slower, uses DNS timeout)
                if self.resolve_hostnames:
                    device.hostname = self.hostname_resolver.resolve(device.ip_address)
                
                enriched_devices.append(device)
                self.device_discovered_signal.emit(device)

            elapsed_time = time.time() - start_time
            
            if self._is_cancelled:
                self.progress_signal.emit(100, "Scan cancelled.", total_devices, len(enriched_devices))
                # Return what we managed to enrich before cancel
                self.finished_signal.emit(enriched_devices, elapsed_time)
            else:
                self.progress_signal.emit(100, "Scan completed.", total_devices, len(enriched_devices))
                self.finished_signal.emit(enriched_devices, elapsed_time)
                
        except PermissionError as pe:
            logger.error(f"Permission error in scan thread: {pe}")
            self.error_signal.emit(str(pe))
        except Exception as e:
            logger.error(f"Unhandled error in scan thread: {e}", exc_info=True)
            self.error_signal.emit(f"Scan failed: {str(e)}")
