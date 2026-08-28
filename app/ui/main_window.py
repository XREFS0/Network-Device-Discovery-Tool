import time
import logging
from pathlib import Path
from typing import List, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QProgressBar, QLabel, QFileDialog, QMessageBox, QToolBar, QStatusBar
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction

from app.core.models import Device, NetworkInterfaceInfo
from app.core.constants import DiscoveryMethod, DeviceStatus
from app.discovery.interface import InterfaceDetector
from app.services.scan_service import ScanService
from app.services.export import ExportService
from app.workers.scan_worker import ScanWorker
from app.ui.widgets.control_panel import ControlPanel
from app.ui.widgets.results_table import ResultsTable
from app.ui.widgets.details_panel import DetailsPanel
from app.ui.dialogs.history_dialog import HistoryDialog

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Network Device Discovery Tool")
        self.resize(1100, 700)
        
        self.scan_service = ScanService()
        self.scan_worker: Optional[ScanWorker] = None
        self.active_scan_id: Optional[int] = None
        self.discovered_devices: List[Device] = []
        
        # Keep track of current scan interface/subnet for the details panel view
        self.current_scan_interface = "Unknown"
        self.current_scan_subnet = "Unknown"
        
        self._setup_ui()
        self._load_interfaces()

    def _setup_ui(self) -> None:
        # Central Widget & Main Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Toolbar
        self._setup_toolbar()

        # Sidebar (Left) - Scan controls
        self.control_panel = ControlPanel(self)
        self.control_panel.start_scan_requested.connect(self._on_start_scan)
        self.control_panel.stop_scan_requested.connect(self._on_stop_scan)
        main_layout.addWidget(self.control_panel)

        # Splitter for Center Table and Right Details
        splitter = QSplitter(Qt.Horizontal, self)
        
        self.results_table = ResultsTable(splitter)
        self.results_table.device_selected.connect(self._on_device_selected)
        
        self.details_panel = DetailsPanel(splitter)
        
        splitter.addWidget(self.results_table)
        splitter.addWidget(self.details_panel)
        splitter.setSizes([700, 300]) # Initial relative widths
        main_layout.addWidget(splitter)

        # Status & Stats Bar (Bottom)
        self._setup_statusbar()

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        # Actions
        history_action = QAction("History", self)
        history_action.triggered.connect(self._on_view_history)
        toolbar.addAction(history_action)

        toolbar.addSeparator()

        self.export_csv_action = QAction("Export CSV", self)
        self.export_csv_action.triggered.connect(self._on_export_csv)
        toolbar.addAction(self.export_csv_action)

        self.export_json_action = QAction("Export JSON", self)
        self.export_json_action.triggered.connect(self._on_export_json)
        toolbar.addAction(self.export_json_action)

        toolbar.addSeparator()

        self.clear_action = QAction("Clear Results", self)
        self.clear_action.triggered.connect(self._on_clear_results)
        toolbar.addAction(self.clear_action)

    def _setup_statusbar(self) -> None:
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Scan Statistics Labels
        self.stats_label = QLabel(self)
        self._update_stats_label(0, 0, 0.0)
        self.status_bar.addWidget(self.stats_label)

    def _update_stats_label(self, discovered: int, processed: int, duration: float) -> None:
        stats_text = f"Devices: {discovered} | Checked: {processed} | Duration: {duration:.2f}s"
        self.stats_label.setText(stats_text)

    def _load_interfaces(self) -> None:
        """Load and populate active interfaces on startup."""
        interfaces = InterfaceDetector.get_interfaces()
        self.control_panel.set_interfaces(interfaces)
        if not interfaces:
            self.status_bar.showMessage("Warning: No active network interfaces detected.", 5000)

    @Slot(str, DiscoveryMethod, str, float, int, bool, bool)
    def _on_start_scan(
        self,
        network_range: str,
        method: DiscoveryMethod,
        interface_name: str,
        timeout: float,
        workers: int,
        resolve_hostnames: bool,
        lookup_vendors: bool
    ) -> None:
        """Initialize scan worker thread and database session, then begin scanning."""
        self._on_clear_results()
        
        self.current_scan_interface = interface_name
        self.current_scan_subnet = network_range
        
        try:
            # 1. Create a session ID in the SQLite database
            self.active_scan_id = self.scan_service.start_scan_session(
                network_range=network_range,
                interface_name=interface_name,
                method=method
            )
        except Exception as e:
            logger.error(f"Failed to start DB session: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to initialize scan session: {e}")
            return

        # 2. Setup Background ScanWorker Thread
        self.scan_worker = ScanWorker(
            network_range=network_range,
            method=method,
            interface_name=interface_name,
            timeout=timeout,
            workers=workers,
            resolve_hostnames=resolve_hostnames,
            lookup_vendors=lookup_vendors
        )
        
        # Connect Signals
        self.scan_worker.started_signal.connect(self._on_scan_started)
        self.scan_worker.progress_signal.connect(self._on_scan_progress)
        self.scan_worker.device_discovered_signal.connect(self._on_device_discovered)
        self.scan_worker.finished_signal.connect(self._on_scan_finished)
        self.scan_worker.error_signal.connect(self._on_scan_error)
        
        # Start Thread
        self.scan_worker.start()

    def _on_stop_scan(self) -> None:
        """Request scan thread cancellation."""
        if self.scan_worker and self.scan_worker.isRunning():
            self.status_bar.showMessage("Stopping scan... Please wait.")
            self.scan_worker.cancel()

    def _on_scan_started(self) -> None:
        self.control_panel.set_scan_state(True)
        self.export_csv_action.setEnabled(False)
        self.export_json_action.setEnabled(False)
        self.clear_action.setEnabled(False)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Scanning network...")
        logger.info("Background scan thread started.")

    @Slot(int, str, int, int)
    def _on_scan_progress(self, percent: int, text: str, processed: int, discovered: int) -> None:
        self.progress_bar.setValue(percent)
        self.status_bar.showMessage(text)
        self._update_stats_label(discovered, processed, 0.0)

    @Slot(Device)
    def _on_device_discovered(self, device: Device) -> None:
        """Receive device from background thread, display immediately in results table."""
        self.discovered_devices.append(device)
        self.results_table.add_device(device)
        self._update_stats_label(len(self.discovered_devices), len(self.discovered_devices), 0.0)

    @Slot(list, float)
    def _on_scan_finished(self, devices: List[Device], elapsed_time: float) -> None:
        """Clean up thread, finalize DB entries, and restore UI controls."""
        self.progress_bar.setVisible(False)
        self.control_panel.set_scan_state(False)
        self.export_csv_action.setEnabled(True)
        self.export_json_action.setEnabled(True)
        self.clear_action.setEnabled(True)
        
        # Update devices table with final enriched lists
        self.discovered_devices = devices
        self.results_table.set_devices(devices)
        
        # Persist results to DB if session exists
        if self.active_scan_id is not None:
            try:
                self.scan_service.complete_scan_session(self.active_scan_id, devices)
            except Exception as e:
                logger.error(f"Error saving results: {e}")
                QMessageBox.warning(self, "Database Error", f"Failed to save results to database: {e}")

        # Update stats
        self._update_stats_label(len(devices), len(devices), elapsed_time)
        
        # Update Status Message
        if self.scan_worker and self.scan_worker.is_cancelled():
            self.status_bar.showMessage("Scan stopped by user.", 5000)
            logger.info("Scan session terminated early.")
        else:
            self.status_bar.showMessage("Scan completed.", 5000)
            logger.info("Scan session finished successfully.")

        self.scan_worker = None

    @Slot(str)
    def _on_scan_error(self, error_msg: str) -> None:
        """Handle errors emitted by the worker thread."""
        self.progress_bar.setVisible(False)
        self.control_panel.set_scan_state(False)
        self.export_csv_action.setEnabled(True)
        self.export_json_action.setEnabled(True)
        self.clear_action.setEnabled(True)
        
        QMessageBox.critical(self, "Scan Error", error_msg)
        self.status_bar.showMessage("Scan failed.", 5000)
        self.scan_worker = None

    @Slot(Device)
    def _on_device_selected(self, device: Device) -> None:
        """Fetch historical records for the selected device and show details."""
        try:
            # Query db for history details
            history = self.scan_service.get_device_history(device.ip_address, device.mac_address)
        except Exception:
            history = {}

        self.details_panel.display_device(
            device=device,
            interface_name=self.current_scan_interface,
            subnet_range=self.current_scan_subnet,
            history_summary=history
        )

    def _on_clear_results(self) -> None:
        self.results_table.clear()
        self.details_panel.clear()
        self.discovered_devices.clear()
        self._update_stats_label(0, 0, 0.0)
        self.status_bar.clearMessage()

    def _on_export_csv(self) -> None:
        if not self.discovered_devices:
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "", "CSV Files (*.csv)")
        if filepath:
            try:
                ExportService.to_csv(self.discovered_devices, Path(filepath))
                self.status_bar.showMessage("Exported successfully to CSV.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to CSV: {e}")

    def _on_export_json(self) -> None:
        if not self.discovered_devices:
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "Export to JSON", "", "JSON Files (*.json)")
        if filepath:
            try:
                ExportService.to_json(self.discovered_devices, Path(filepath))
                self.status_bar.showMessage("Exported successfully to JSON.", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export to JSON: {e}")

    def _on_view_history(self) -> None:
        dialog = HistoryDialog(self.scan_service, self)
        dialog.scan_loaded.connect(self._on_load_past_scan)
        dialog.exec()

    @Slot(int)
    def _on_load_past_scan(self, scan_id: int) -> None:
        """Load scan results from a past session."""
        self._on_clear_results()
        try:
            # Find scan metadata to display correct settings in details
            scans = self.scan_service.get_history()
            past_scan = next((s for s in scans if s.id == scan_id), None)
            
            if past_scan:
                self.current_scan_interface = past_scan.interface_name
                self.current_scan_subnet = past_scan.network_range
                
            devices = self.scan_service.get_scan_results(scan_id)
            self.discovered_devices = devices
            self.results_table.set_devices(devices)
            self._update_stats_label(len(devices), len(devices), 0.0)
            self.status_bar.showMessage(f"Loaded {len(devices)} devices from Scan #{scan_id}.", 5000)
        except Exception as e:
            logger.error(f"Error loading past scan {scan_id}: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load scan results: {e}")

    def closeEvent(self, event) -> None:
        """Safely close thread workers on window exit."""
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.cancel()
            self.scan_worker.wait()
        event.accept()
