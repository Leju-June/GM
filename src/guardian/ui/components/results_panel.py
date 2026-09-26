from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QCheckBox, QTabWidget, QLabel
)
from PySide6.QtCore import Qt, Signal

class ResultsPanel(QWidget):
    finding_selected = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.findings = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("필터:"))
        
        self.filter_homoglyph = QCheckBox("HOMOGLYPH")
        self.filter_homoglyph.setChecked(True)
        self.filter_jamo = QCheckBox("JAMO")
        self.filter_jamo.setChecked(True)
        self.filter_transparent = QCheckBox("TRANSPARENT")
        self.filter_transparent.setChecked(True)
        self.filter_offscreen = QCheckBox("OFFSCREEN")
        self.filter_offscreen.setChecked(True)
        
        for cb in (self.filter_homoglyph, self.filter_jamo, self.filter_transparent, self.filter_offscreen):
            filter_layout.addWidget(cb)
            cb.stateChanged.connect(self.refresh_table)
            
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Main Results Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["기법", "위치(URL/Iframe)", "증거 텍스트", "위험도"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        self.tabs.addTab(self.table, "탐지 목록")
        
        # Uncertain Table
        self.uncertain_table = QTableWidget(0, 4)
        self.uncertain_table.setHorizontalHeaderLabels(["기법", "위치(URL/Iframe)", "증거 텍스트", "위험도"])
        self.uncertain_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.uncertain_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.uncertain_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.tabs.addTab(self.uncertain_table, "불확실 후보(검토요망)")
        
        layout.addWidget(self.tabs)
        
    def add_finding(self, finding: dict):
        self.findings.append(finding)
        self.refresh_table()
        
    def refresh_table(self):
        self.table.setRowCount(0)
        
        active_filters = []
        if self.filter_homoglyph.isChecked(): active_filters.append("HOMOGLYPH")
        if self.filter_jamo.isChecked(): active_filters.append("JAMO")
        if self.filter_transparent.isChecked(): active_filters.append("TRANSPARENT")
        if self.filter_offscreen.isChecked(): active_filters.append("OFFSCREEN")
        
        for f in self.findings:
            if f.get("technique") not in active_filters:
                continue
                
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            tech_item = QTableWidgetItem(f.get("technique", ""))
            url_item = QTableWidgetItem(f.get("url", ""))
            text_item = QTableWidgetItem(f.get("evidence_text", ""))
            score_item = QTableWidgetItem(str(f.get("score", "High")))
            
            # Store full data in first item
            tech_item.setData(Qt.UserRole, f)
            
            self.table.setItem(row, 0, tech_item)
            self.table.setItem(row, 1, url_item)
            self.table.setItem(row, 2, text_item)
            self.table.setItem(row, 3, score_item)
            
    def _on_selection_changed(self):
        selected = self.table.selectedItems()
        if selected:
            # First column item has the data
            row = selected[0].row()
            item = self.table.item(row, 0)
            if item:
                finding = item.data(Qt.UserRole)
                self.finding_selected.emit(finding)
