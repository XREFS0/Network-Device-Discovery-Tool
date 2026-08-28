from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox,
    QLineEdit, QDoubleSpinBox, QSpinBox, QCheckBox, QPushButton,
    QLabel, QGroupBox
)
from PySide6.QtCore import Signal
from app.core.models import NetworkInterfaceInfo
from app.core.constants import DiscoveryMethod
from app.core.config import Config

class ControlPanel(QWidget):
    # Signals
    start_scan_requested = Signal(str, DiscoveryMethod, str, float, int, bool, bool) # range, method, interface, timeout, workers, hostname, vendor
    stop_scan_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._interfaces: List[NetworkInterfaceInfo] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Network Target Group
        target_group = QGroupBox("Network Configuration", self)
        target_layout = QFormLayout(target_group)
        
        self.interface_combo = QComboBox(self)
        self.interface_combo.currentIndexChanged.connect(self._on_interface_changed)
        target_layout.addRow("Interface:", self.interface_combo)

        self.range_input = QLineEdit(self)
        self.range_input.setPlaceholderText("e.g. 192.168.1.0/24")
        target_layout.addRow("Subnet Range:", self.range_input)
        
        layout.addWidget(target_group)

        # Settings Group
        settings_group = QGroupBox("Scan Parameters", self)
        settings_layout = QFormLayout(settings_group)

        self.method_combo = QComboBox(self)
        for method in DiscoveryMethod:
            self.method_combo.addItem(method.value, method)
        settings_layout.addRow("Method:", self.method_combo)

        self.timeout_spin = QDoubleSpinBox(self)
        self.timeout_spin.setRange(0.1, 10.0)
        self.timeout_spin.setSingleStep(0.1)
        self.timeout_spin.setValue(Config.DEFAULT_TIMEOUT)
        self.timeout_spin.setSuffix(" sec")
        settings_layout.addRow("Timeout:", self.timeout_spin)

        self.workers_spin = QSpinBox(self)
        self.workers_spin.setRange(1, 100)
        self.workers_spin.setValue(Config.DEFAULT_WORKERS)
        settings_layout.addRow("Concurrency:", self.workers_spin)

        self.resolve_hostnames_check = QCheckBox(self)
        self.resolve_hostnames_check.setChecked(Config.DEFAULT_RESOLVE_HOSTNAMES)
        settings_layout.addRow("Resolve Hostnames:", self.resolve_hostnames_check)

        self.lookup_vendors_check = QCheckBox(self)
        self.lookup_vendors_check.setChecked(Config.DEFAULT_LOOKUP_VENDORS)
        settings_layout.addRow("Lookup Vendors:", self.lookup_vendors_check)

        layout.addWidget(settings_group)

        # Actions
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Scan", self)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.start_btn.setDefault(True)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop Scan", self)
        self.stop_btn.clicked.connect(self.stop_scan_requested.emit)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def set_interfaces(self, interfaces: List[NetworkInterfaceInfo]) -> None:
        """Populate the interface list combobox."""
        self.interface_combo.blockSignals(True)
        self.interface_combo.clear()
        self._interfaces = interfaces
        
        for iface in interfaces:
            display_text = f"{iface.name}"
            if iface.ip_address:
                display_text += f" ({iface.ip_address})"
            self.interface_combo.addItem(display_text, iface)
            
        self.interface_combo.blockSignals(False)
        
        # Trigger change to update subnet range input
        if interfaces:
            self.interface_combo.setCurrentIndex(0)
            self._on_interface_changed(0)

    def _on_interface_changed(self, index: int) -> None:
        """Update subnet range text when interface is changed."""
        if index < 0 or index >= len(self._interfaces):
            return
        iface = self._interfaces[index]
        if iface.network_range:
            self.range_input.setText(iface.network_range)
        else:
            self.range_input.clear()

    def _on_start_clicked(self) -> None:
        network_range = self.range_input.text().strip()
        if not network_range:
            return

        method = self.method_combo.currentData()
        
        # Get selected interface name
        interface_name = ""
        current_idx = self.interface_combo.currentIndex()
        if current_idx >= 0 and current_idx < len(self._interfaces):
            interface_name = self._interfaces[current_idx].name

        timeout = self.timeout_spin.value()
        workers = self.workers_spin.value()
        resolve_hostnames = self.resolve_hostnames_check.isChecked()
        lookup_vendors = self.lookup_vendors_check.isChecked()

        self.start_scan_requested.emit(
            network_range, method, interface_name, timeout, workers, resolve_hostnames, lookup_vendors
        )

    def set_scan_state(self, scanning: bool) -> None:
        """Enable/Disable controls during scanning state."""
        self.start_btn.setEnabled(not scanning)
        self.stop_btn.setEnabled(scanning)
        self.interface_combo.setEnabled(not scanning)
        self.range_input.setEnabled(not scanning)
        self.method_combo.setEnabled(not scanning)
        self.timeout_spin.setEnabled(not scanning)
        self.workers_spin.setEnabled(not scanning)
        self.resolve_hostnames_check.setEnabled(not scanning)
        self.lookup_vendors_check.setEnabled(not scanning)
