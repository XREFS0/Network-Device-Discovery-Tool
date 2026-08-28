from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QGroupBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt
from app.core.models import Device

class DetailsPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self.title_label = QLabel("Device Details", self)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        # Empty State
        self.empty_label = QLabel("Select a device from the list to view detailed discovery information.", self)
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; font-style: italic; margin-top: 20px;")
        layout.addWidget(self.empty_label)

        # Scroll Area for Details
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_area.setVisible(False)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        # General Group
        gen_group = QGroupBox("General Info", scroll_widget)
        gen_layout = QFormLayout(gen_group)
        gen_layout.setSpacing(8)
        self.ip_lbl = QLabel("-")
        self.ip_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.mac_lbl = QLabel("-")
        self.mac_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.host_lbl = QLabel("-")
        self.host_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.vendor_lbl = QLabel("-")
        self.vendor_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_lbl = QLabel("-")
        
        gen_layout.addRow("IP Address:", self.ip_lbl)
        gen_layout.addRow("MAC Address:", self.mac_lbl)
        gen_layout.addRow("Hostname:", self.host_lbl)
        gen_layout.addRow("Vendor:", self.vendor_lbl)
        gen_layout.addRow("Status:", self.status_lbl)
        scroll_layout.addWidget(gen_group)

        # Network Group
        net_group = QGroupBox("Network Properties", scroll_widget)
        net_layout = QFormLayout(net_group)
        net_layout.setSpacing(8)
        self.iface_lbl = QLabel("-")
        self.subnet_lbl = QLabel("-")
        self.method_lbl = QLabel("-")
        self.rtt_lbl = QLabel("-")

        net_layout.addRow("Interface:", self.iface_lbl)
        net_layout.addRow("Subnet Range:", self.subnet_lbl)
        net_layout.addRow("Discovery Method:", self.method_lbl)
        net_layout.addRow("Response Time:", self.rtt_lbl)
        scroll_layout.addWidget(net_group)

        # History Group
        hist_group = QGroupBox("Discovery History", scroll_widget)
        hist_layout = QFormLayout(hist_group)
        hist_layout.setSpacing(8)
        self.first_seen_lbl = QLabel("-")
        self.last_seen_lbl = QLabel("-")
        self.count_lbl = QLabel("-")

        hist_layout.addRow("First Seen:", self.first_seen_lbl)
        hist_layout.addRow("Last Seen:", self.last_seen_lbl)
        hist_layout.addRow("Times Discovered:", self.count_lbl)
        scroll_layout.addWidget(hist_group)

        scroll_layout.addStretch()
        self.scroll_area.setWidget(scroll_widget)
        layout.addWidget(self.scroll_area)

    def display_device(
        self,
        device: Device,
        interface_name: str,
        subnet_range: str,
        history_summary: Dict[str, Any]
    ) -> None:
        """Populate and show the detailed information of the device."""
        self.empty_label.setVisible(False)
        self.scroll_area.setVisible(True)

        self.ip_lbl.setText(device.ip_address)
        self.mac_lbl.setText(device.mac_address)
        self.host_lbl.setText(device.hostname)
        self.vendor_lbl.setText(device.vendor)
        self.status_lbl.setText(device.status.value)
        
        # Color code status
        if device.status.value == "Online":
            self.status_lbl.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_lbl.setStyleSheet("color: gray;")

        self.iface_lbl.setText(interface_name if interface_name else "Unknown")
        self.subnet_lbl.setText(subnet_range if subnet_range else "Unknown")
        self.method_lbl.setText(device.method.value)
        self.rtt_lbl.setText(f"{device.response_time_ms} ms" if device.response_time_ms is not None else "Unknown")

        # History data
        first_seen = history_summary.get("first_seen", device.first_seen)
        last_seen = history_summary.get("last_seen", device.last_seen)
        # Use database history count plus 1 if we're scanning right now, or whatever has been fetched.
        count = history_summary.get("discovery_count", device.discovery_count)
        
        self.first_seen_lbl.setText(str(first_seen))
        self.last_seen_lbl.setText(str(last_seen))
        self.count_lbl.setText(str(count))

    def clear(self) -> None:
        """Clear detail fields and display default empty label."""
        self.scroll_area.setVisible(False)
        self.empty_label.setVisible(True)
