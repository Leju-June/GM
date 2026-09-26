from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QSpinBox, QGroupBox, QDoubleSpinBox
)
from PySide6.QtCore import Signal

class SettingsPanel(QWidget):
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group_box = QGroupBox("스캔 설정 (Scan Settings)")
        form_layout = QFormLayout(group_box)
        
        self.max_pages_spin = QSpinBox()
        self.max_pages_spin.setRange(1, 10000)
        self.max_pages_spin.setValue(500)
        
        self.max_depth_spin = QSpinBox()
        self.max_depth_spin.setRange(1, 20)
        self.max_depth_spin.setValue(6)
        
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 10)
        self.concurrency_spin.setValue(2)
        
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(1.0, 60.0)
        self.timeout_spin.setValue(30.0)
        
        form_layout.addRow("최대 탐색 페이지 수:", self.max_pages_spin)
        form_layout.addRow("최대 링크 깊이:", self.max_depth_spin)
        form_layout.addRow("동시성 (Concurrency):", self.concurrency_spin)
        form_layout.addRow("타임아웃 (초):", self.timeout_spin)
        
        layout.addWidget(group_box)
        
        # Connect signals
        self.max_pages_spin.valueChanged.connect(self._emit_settings)
        self.max_depth_spin.valueChanged.connect(self._emit_settings)
        self.concurrency_spin.valueChanged.connect(self._emit_settings)
        self.timeout_spin.valueChanged.connect(self._emit_settings)
        
    def _emit_settings(self):
        self.settings_changed.emit(self.get_settings())
        
    def get_settings(self) -> dict:
        return {
            "max_pages": self.max_pages_spin.value(),
            "max_depth": self.max_depth_spin.value(),
            "concurrency": self.concurrency_spin.value(),
            "timeout_sec": self.timeout_spin.value()
        }
