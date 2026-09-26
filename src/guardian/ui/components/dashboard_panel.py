from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGroupBox, QFrame
)
from PySide6.QtCore import Qt

class DashboardPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group_box = QGroupBox("실시간 지표 (Real-time Dashboard)")
        grid_layout = QHBoxLayout(group_box)
        
        # Helper to create styled labels
        def create_metric_widget(title, default_val):
            container = QWidget()
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(5, 5, 5, 5)
            
            title_lbl = QLabel(title)
            title_lbl.setAlignment(Qt.AlignCenter)
            title_lbl.setStyleSheet("color: #666; font-size: 11px;")
            
            val_lbl = QLabel(default_val)
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
            
            v_layout.addWidget(title_lbl)
            v_layout.addWidget(val_lbl)
            
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setLayout(v_layout)
            return frame, val_lbl
            
        self.metric_frames = []
        
        frame, self.elapsed_lbl = create_metric_widget("경과 시간", "00:00")
        grid_layout.addWidget(frame)
        
        frame, self.visited_lbl = create_metric_widget("방문 페이지", "0")
        grid_layout.addWidget(frame)
        
        frame, self.queue_lbl = create_metric_widget("대기 큐", "0")
        grid_layout.addWidget(frame)
        
        frame, self.iframe_lbl = create_metric_widget("iframe 검사", "0")
        grid_layout.addWidget(frame)
        
        frame, self.fail_lbl = create_metric_widget("실패/경고", "0")
        grid_layout.addWidget(frame)
        
        layout.addWidget(group_box)
        
    def update_metrics(self, data: dict):
        if "elapsed" in data:
            self.elapsed_lbl.setText(data["elapsed"])
        if "visited" in data:
            self.visited_lbl.setText(str(data["visited"]))
        if "queue" in data:
            self.queue_lbl.setText(str(data["queue"]))
        if "iframes" in data:
            self.iframe_lbl.setText(str(data["iframes"]))
        if "fails" in data:
            self.fail_lbl.setText(str(data["fails"]))
