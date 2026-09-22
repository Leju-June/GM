import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QTextEdit, QLabel
)
from PySide6.QtCore import QProcess, Slot

from guardian.ipc.protocol import decode_message, encode_message

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("공공웹 클린 가디언 (Public Web Clean Guardian)")
        self.resize(800, 600)
        
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        
        # URL Input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("검사할 웹사이트 URL (예: https://example.com)")
        self.start_btn = QPushButton("탐지 시작")
        self.start_btn.clicked.connect(self.start_scan)
        
        url_layout.addWidget(QLabel("입력 URL:"))
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.start_btn)
        
        layout.addLayout(url_layout)
        
        # Log Output
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(QLabel("탐지 로그:"))
        layout.addWidget(self.log_output)
        
        self.setCentralWidget(main_widget)
        
        self.process = None
        
    @Slot()
    def start_scan(self):
        url = self.url_input.text().strip()
        if not url:
            return
            
        self.log_output.clear()
        self.log_output.append(f"준비 중... {url}")
        self.start_btn.setEnabled(False)
        
        worker_script = os.path.join(os.path.dirname(__file__), '..', 'worker', 'process.py')
        
        self.process = QProcess(self)
        self.process.setProgram(sys.executable)
        self.process.setArguments([worker_script])
        
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
        self.process.start()
        
        # Send START message
        msg = encode_message("START", {"url": url, "output_path": "result.json"})
        self.process.write((msg + "\n").encode('utf-8'))
        
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
                    self.log_output.append(f"[시작] {msg.payload.get('url')} 탐지 시작...")
                elif msg.type == "FINDING":
                    f = msg.payload
                    self.log_output.append(f"[발견] {f.get('technique')} - {f.get('evidence_text')} (경로: {f.get('location')})")
                elif msg.type == "COMPLETED":
                    self.log_output.append(f"[완료] 총 {msg.payload.get('scanned_count')} 페이지 검사 완료. 발견 건수: {msg.payload.get('findings_count')}")
                    self.log_output.append(f"결과 저장 위치: {msg.payload.get('output_path')}")
                elif msg.type == "ERROR":
                    self.log_output.append(f"[오류] {msg.payload.get('message')}")
            else:
                self.log_output.append(f"Worker Output: {line}")
                
    @Slot()
    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8')
        for line in data.splitlines():
            if line.strip():
                self.log_output.append(f"Worker Error: {line.strip()}")
                
    @Slot(int, QProcess.ExitStatus)
    def process_finished(self, exit_code, exit_status):
        self.log_output.append("작업 프로세스 종료.")
        self.start_btn.setEnabled(True)
