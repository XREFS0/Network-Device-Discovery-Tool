from typing import List, Any
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from app.core.models import Device

class DevicesTableModel(QAbstractTableModel):
    COLUMNS = [
        "Status",
        "IP Address",
        "MAC Address",
        "Hostname",
        "Vendor",
        "Method",
        "Response Time",
        "First Seen",
        "Last Seen"
    ]

    def __init__(self, devices: List[Device] = None) -> None:
        super().__init__()
        self._devices: List[Device] = devices or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._devices)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._devices)):
            return None

        device = self._devices[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return device.status.value
            elif col == 1:
                return device.ip_address
            elif col == 2:
                return device.mac_address
            elif col == 3:
                return device.hostname
            elif col == 4:
                return device.vendor
            elif col == 5:
                return device.method.value
            elif col == 6:
                return f"{device.response_time_ms} ms" if device.response_time_ms is not None else "Unknown"
            elif col == 7:
                return device.first_seen
            elif col == 8:
                return device.last_seen
                
        elif role == Qt.TextAlignmentRole:
            if col in (6, 7, 8):  # Numbers/dates right or center aligned
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def get_device(self, row: int) -> Device:
        return self._devices[row]

    def set_devices(self, devices: List[Device]) -> None:
        self.beginResetModel()
        self._devices = list(devices)
        self.endResetModel()

    def add_device(self, device: Device) -> None:
        # Check if device with this IP is already in list (update it)
        for i, existing in enumerate(self._devices):
            if existing.ip_address == device.ip_address:
                self._devices[i] = device
                # Notify table update
                self.dataChanged.emit(self.index(i, 0), self.index(i, len(self.COLUMNS) - 1))
                return

        # Otherwise append new device
        self.beginInsertRows(QModelIndex(), len(self._devices), len(self._devices))
        self._devices.append(device)
        self.endInsertRows()

    def clear(self) -> None:
        self.beginResetModel()
        self._devices.clear()
        self.endResetModel()

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        self.layoutAboutToBeChanged.emit()
        reverse = (order == Qt.DescendingOrder)
        
        def sort_key(device: Device):
            if column == 0:
                return device.status.value
            elif column == 1:
                # Sort IP addresses numerically rather than lexicographically
                try:
                    import ipaddress
                    return ipaddress.IPv4Address(device.ip_address)
                except ValueError:
                    return device.ip_address
            elif column == 2:
                return device.mac_address
            elif column == 3:
                return device.hostname
            elif column == 4:
                return device.vendor
            elif column == 5:
                return device.method.value
            elif column == 6:
                return device.response_time_ms if device.response_time_ms is not None else -1
            elif column == 7:
                return device.first_seen
            elif column == 8:
                return device.last_seen
            return ""

        self._devices.sort(key=sort_key, reverse=reverse)
        self.layoutChanged.emit()
