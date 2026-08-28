from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QAbstractItemView, QWidget
)
from PySide6.QtCore import Qt, Signal
from app.core.models import ScanInfo
from app.services.scan_service import ScanService

class HistoryDialog(QDialog):
    # Signals
    scan_loaded = Signal(int) # Emits the scan_id to load

    def __init__(self, scan_service: ScanService, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scan_service = scan_service
        self.setWindowTitle("Scan History")
        self.resize(750, 400)
        self._setup_ui()
        self._load_history()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Table Widget
        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Scan ID", "Start Time", "End Time", "Network Range", "Interface", "Method", "Devices Found"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        layout.addWidget(self.table)

        # Buttons Layout
        btn_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Open Scan Results", self)
        self.load_btn.clicked.connect(self._on_load_clicked)
        self.load_btn.setEnabled(False)
        btn_layout.addWidget(self.load_btn)

        self.delete_btn = QPushButton("Delete Scan", self)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)

        self.clear_all_btn = QPushButton("Clear All History", self)
        self.clear_all_btn.clicked.connect(self._on_clear_all_clicked)
        btn_layout.addWidget(self.clear_all_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton("Close", self)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

        # Connection to enable/disable buttons based on selection
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

    def _load_history(self) -> None:
        """Load history records from the database and populate the table."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        try:
            self._scans: List[ScanInfo] = self.scan_service.get_history()
            self.table.setRowCount(len(self._scans))
            
            for idx, scan in enumerate(self._scans):
                self.table.setItem(idx, 0, QTableWidgetItem(str(scan.id)))
                self.table.setItem(idx, 1, QTableWidgetItem(scan.start_time))
                self.table.setItem(idx, 2, QTableWidgetItem(scan.end_time or "Incomplete"))
                self.table.setItem(idx, 3, QTableWidgetItem(scan.network_range))
                self.table.setItem(idx, 4, QTableWidgetItem(scan.interface_name))
                self.table.setItem(idx, 5, QTableWidgetItem(scan.discovery_method.value))
                self.table.setItem(idx, 6, QTableWidgetItem(str(scan.device_count)))
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load scan history: {e}")
            
        self.table.blockSignals(False)
        self._on_selection_changed()

    def _on_selection_changed(self) -> None:
        selected = len(self.table.selectedItems()) > 0
        self.load_btn.setEnabled(selected)
        self.delete_btn.setEnabled(selected)

    def _on_load_clicked(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._scans):
            return
        
        scan_id = self._scans[row].id
        if scan_id is not None:
            self.scan_loaded.emit(scan_id)
            self.accept()

    def _on_delete_clicked(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._scans):
            return
            
        scan = self._scans[row]
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete scan #{scan.id} (started {scan.start_time})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if scan.id is not None:
                    self.scan_service.delete_scan(scan.id)
                    self._load_history()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete scan: {e}")

    def _on_clear_all_clicked(self) -> None:
        if not self._scans:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Clear All",
            "Are you sure you want to delete ALL scan history from the database? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.scan_service.clear_all_history()
                self._load_history()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear history: {e}")
