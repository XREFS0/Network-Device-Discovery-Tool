from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLineEdit,
    QLabel, QMenu, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QAction, QGuiApplication
from app.core.models import Device
from app.ui.models.devices_table_model import DevicesTableModel

class ResultsTable(QWidget):
    # Signals
    device_selected = Signal(Device)
    device_double_clicked = Signal(Device)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search Bar layout
        search_layout = QHBoxLayout()
        search_label = QLabel("Filter results:", self)
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search by IP, MAC, hostname, vendor...")
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Models Setup
        self.table_model = DevicesTableModel()
        
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.table_model)
        self.proxy_model.setFilterKeyColumn(-1)  # Search all columns
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        # Table View Setup
        self.table_view = QTableView(self)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.setAlternatingRowColors(True)
        
        # Header configuration
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)
        
        # Connections
        self.table_view.doubleClicked.connect(self._on_double_clicked)
        self.table_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

        # Context Menu
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table_view)

    def _on_search_changed(self, text: str) -> None:
        self.proxy_model.setFilterFixedString(text)

    def _on_selection_changed(self) -> None:
        device = self.get_selected_device()
        if device:
            self.device_selected.emit(device)

    def _on_double_clicked(self, proxy_index: QModelIndex) -> None:
        source_index = self.proxy_model.mapToSource(proxy_index)
        device = self.table_model.get_device(source_index.row())
        self.device_double_clicked.emit(device)

    def get_selected_device(self) -> Optional[Device]:
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            return None
        proxy_index = indexes[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        return self.table_model.get_device(source_index.row())

    def _show_context_menu(self, pos) -> None:
        index = self.table_view.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)
        
        copy_cell_action = QAction("Copy value", self)
        copy_cell_action.triggered.connect(lambda: self._copy_cell_value(index))
        menu.addAction(copy_cell_action)

        copy_row_action = QAction("Copy row", self)
        copy_row_action.triggered.connect(lambda: self._copy_row_value(index))
        menu.addAction(copy_row_action)

        menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def _copy_cell_value(self, proxy_index: QModelIndex) -> None:
        value = self.proxy_model.data(proxy_index, Qt.DisplayRole)
        if value:
            # Strip " ms" suffix if copying RTT
            val_str = str(value)
            QGuiApplication.clipboard().setText(val_str)

    def _copy_row_value(self, proxy_index: QModelIndex) -> None:
        row = proxy_index.row()
        cols = self.proxy_model.columnCount()
        row_values = []
        for col in range(cols):
            val = self.proxy_model.data(self.proxy_model.index(row, col), Qt.DisplayRole)
            row_values.append(str(val) if val else "")
        
        QGuiApplication.clipboard().setText("\t".join(row_values))

    def set_devices(self, devices: list) -> None:
        self.table_model.set_devices(devices)
        self._resize_columns()

    def add_device(self, device: Device) -> None:
        self.table_model.add_device(device)
        self._resize_columns()

    def clear(self) -> None:
        self.table_model.clear()

    def _resize_columns(self) -> None:
        # Resize columns to content, but keep minimum reasonable widths
        self.table_view.resizeColumnsToContents()
        for col in range(self.table_model.columnCount()):
            width = self.table_view.columnWidth(col)
            if width < 80:
                self.table_view.setColumnWidth(col, 80)
            elif width > 300:
                self.table_view.setColumnWidth(col, 300)
