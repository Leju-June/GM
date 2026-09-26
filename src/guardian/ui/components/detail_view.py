from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QTextEdit, QScrollArea, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

class DetailView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group_box = QGroupBox("상세 증거 (Evidence Details)")
        main_layout = QVBoxLayout(group_box)
        
        # Text Comparison
        text_layout = QHBoxLayout()
        
        self.orig_text = QTextEdit()
        self.orig_text.setReadOnly(True)
        self.orig_text.setPlaceholderText("원문 텍스트")
        
        self.norm_text = QTextEdit()
        self.norm_text.setReadOnly(True)
        self.norm_text.setPlaceholderText("정규화 텍스트 (변환 후)")
        
        text_layout.addWidget(self.orig_text)
        text_layout.addWidget(self.norm_text)
        
        main_layout.addWidget(QLabel("텍스트 비교:"))
        main_layout.addLayout(text_layout)
        
        # Rule & Selector Info
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(100)
        self.info_text.setPlaceholderText("매칭된 규칙, CSS 스타일, 고유 셀렉터 정보 등")
        
        main_layout.addWidget(QLabel("상세 정보:"))
        main_layout.addWidget(self.info_text)
        
        # Screenshot Preview
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.screenshot_lbl = QLabel("스크린샷 (선택 시 표시)")
        self.screenshot_lbl.setAlignment(Qt.AlignCenter)
        self.screenshot_lbl.setStyleSheet("background-color: #eee; color: #888;")
        
        self.scroll_area.setWidget(self.screenshot_lbl)
        
        main_layout.addWidget(QLabel("스크린샷 미리보기:"))
        main_layout.addWidget(self.scroll_area)
        
        layout.addWidget(group_box)
        
    def set_finding(self, finding: dict):
        if not finding:
            self.clear()
            return
            
        orig = finding.get("evidence_text", "")
        # For now we just show the same text or empty if no normalized data exists
        norm = finding.get("normalized_text", orig)
        
        self.orig_text.setText(orig)
        self.norm_text.setText(norm)
        
        info = []
        info.append(f"기법: {finding.get('technique')}")
        info.append(f"위치(경로): {finding.get('location')}")
        info.append(f"URL: {finding.get('url')}")
        
        # Future-proofing: display css evidence if present
        if "css_evidence" in finding:
            info.append(f"CSS 증거: {finding['css_evidence']}")
            
        self.info_text.setText("\n".join(info))
        
        # Screenshot
        screenshot_path = finding.get("screenshot_path")
        if screenshot_path:
            pixmap = QPixmap(screenshot_path)
            if not pixmap.isNull():
                self.screenshot_lbl.setPixmap(pixmap.scaled(
                    self.scroll_area.width() - 20, 
                    800, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                ))
            else:
                self.screenshot_lbl.setText("이미지를 불러올 수 없습니다.")
        else:
            self.screenshot_lbl.setText("스크린샷 없음")
            
    def clear(self):
        self.orig_text.clear()
        self.norm_text.clear()
        self.info_text.clear()
        self.screenshot_lbl.clear()
        self.screenshot_lbl.setText("스크린샷 (선택 시 표시)")
