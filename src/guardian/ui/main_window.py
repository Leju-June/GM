import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QSplitter, QMessageBox
)
from PySide6.QtCore import QProcess, Slot, Qt, QTimer

from guardian.ipc.protocol import decode_message, encode_message
from guardian.ui.components import SettingsPanel, DashboardPanel, ResultsPanel, DetailView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("공공웹 클린 가디언 (Public Web Clean Guardian)")
        self.resize(1200, 800)
        
        self.init_ui()
        
        self.process = None
        self.is_scanning = False
        
    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # Top Bar: URL and Actions
        top_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("검사할 웹사이트 URL (예: https://example.com)")
        self.start_btn = QPushButton("탐지 시작")
        self.start_btn.clicked.connect(self.start_scan)
        
        self.cancel_btn = QPushButton("취소 (Cancel)")
        self.cancel_btn.clicked.connect(self.cancel_scan)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("color: red;")
        
        top_layout.addWidget(self.url_input)
        top_layout.addWidget(self.start_btn)
        top_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(top_layout)
        
        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel (Settings & Dashboard)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.settings_panel = SettingsPanel()
        self.dashboard_panel = DashboardPanel()
        
        left_layout.addWidget(self.settings_panel)
        left_layout.addWidget(self.dashboard_panel)
        left_layout.addStretch()
        
        # Center Panel (Results)
        self.results_panel = ResultsPanel()
        self.results_panel.finding_selected.connect(self._on_finding_selected)
        
        # Right Panel (Detail View)
        self.detail_view = DetailView()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(self.results_panel)
        splitter.addWidget(self.detail_view)
        
        splitter.setSizes([300, 500, 400])
        
        layout.addWidget(splitter)
        
        self.setCentralWidget(main_widget)
        
    @Slot()
    def start_scan(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "경고", "URL을 입력하세요.")
            return
            
        self.is_scanning = True
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.settings_panel.setEnabled(False)
        self.url_input.setEnabled(False)
        
        # Reset panels
        self.results_panel.findings = []
        self.results_panel.refresh_table()
        self.detail_view.clear()
        
        self.process = QProcess(self)
        self.process.setProgram(sys.executable)
        
        # Use python -m guardian --worker for PyInstaller compatibility
        if getattr(sys, 'frozen', False):
            # In PyInstaller, sys.executable is the .exe itself
            self.process.setArguments(["--worker"])
        else:
            self.process.setArguments(["-m", "guardian", "--worker"])
            
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        self.process.start()
        
        settings = self.settings_panel.get_settings()
        
        # Send START message
        payload = {
            "url": url, 
            "output_path": "result.json",
            "settings": settings
        }
        msg = encode_message("START", payload)
        self.process.write((msg + "\n").encode('utf-8'))
        
    @Slot()
    def cancel_scan(self):
        if self.process and self.process.state() == QProcess.Running:
            msg = encode_message("CANCEL", {})
            self.process.write((msg + "\n").encode('utf-8'))
            self.cancel_btn.setEnabled(False)
            
            # Start a timer to force kill if it doesn't close gracefully
            QTimer.singleShot(5000, self._force_kill_process)
            
    def _force_kill_process(self):
        if self.process and self.process.state() == QProcess.Running:
            self.process.kill()
            
    @Slot()
    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8')
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
                
            msg = decode_message(line)
            if msg:
                if msg.type == "STARTED":
                    pass # Handled on GUI
                elif msg.type == "FINDING":
                    self.results_panel.add_finding(msg.payload)
                elif msg.type == "COMPLETED":
                    self.dashboard_panel.update_metrics({
                        "visited": msg.payload.get('scanned_count', 0)
                    })
                elif msg.type == "ERROR":
                    QMessageBox.critical(self, "오류", msg.payload.get('message', '알 수 없는 오류'))
                elif msg.type == "METRICS":
                    # Update real-time metrics
                    self.dashboard_panel.update_metrics(msg.payload)
            else:
                pass # Unstructured log
                
    @Slot()
    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8')
        # Here we could log stderr to a file or hidden console
                
    @Slot(int, QProcess.ExitStatus)
    def process_finished(self, exit_code, exit_status):
        self.is_scanning = False
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.settings_panel.setEnabled(True)
        self.url_input.setEnabled(True)
        
        if exit_code != 0:
            print(f"Process exited abnormally with code {exit_code}")
            
    @Slot(dict)
    def _on_finding_selected(self, finding):
        self.detail_view.set_finding(finding)
