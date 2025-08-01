import sys
import os
import threading
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                            QTableWidget, QTableWidgetItem, QTabWidget,
                            QGroupBox, QGridLayout, QStatusBar, QHeaderView)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont

# 현재 파일의 디렉토리에서 상위 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from server import LiveConServer
from server_module.sql_utils import connect_to_database

class ServerCallbackHandler:
    """서버 이벤트를 GUI로 전달하는 핸들러"""
    def __init__(self, gui_instance):
        self.gui = gui_instance
    
    def on_log(self, message):
        self.gui.log_signal.emit(message)
    
    def on_client_connected(self, client_addr):
        self.gui.client_connected_signal.emit(client_addr)
    
    def on_client_disconnected(self, client_addr):
        self.gui.client_disconnected_signal.emit(client_addr)
    
    def on_data_received(self, data, client_addr):
        self.gui.data_received_signal.emit(data, client_addr)

class ServerWorker(QThread):
    """서버를 별도 스레드에서 실행하는 워커"""
    server_started = pyqtSignal(bool)
    
    def __init__(self, callback_handler):
        super().__init__()
        self.callback_handler = callback_handler
        self.server = None
        
    def run(self):
        """서버 실행"""
        # 테스트 모드로 서버 시작 (데이터베이스 검증 우회)
        self.server = LiveConServer(port=12347, callback_handler=self.callback_handler, skip_db_validation=True)
        success = self.server.start()
        self.server_started.emit(success)
    
    def stop_server(self):
        """서버 중지"""
        if self.server:
            self.server.stop()
            
    def get_connected_clients(self):
        """연결된 클라이언트 목록 반환"""
        if self.server:
            return self.server.get_connected_clients()
        return []

class LiveConServerGUI(QMainWindow):
    # GUI 시그널 정의
    log_signal = pyqtSignal(str)
    client_connected_signal = pyqtSignal(str)
    client_disconnected_signal = pyqtSignal(str)
    data_received_signal = pyqtSignal(dict, str)
    
    def __init__(self):
        super().__init__()
        self.server_worker = None
        self.connected_clients = set()
        self.callback_handler = ServerCallbackHandler(self)
        
        # 시그널 연결
        self.log_signal.connect(self.add_log)
        self.client_connected_signal.connect(self.on_client_connected)
        self.client_disconnected_signal.connect(self.on_client_disconnected)
        self.data_received_signal.connect(self.on_data_received)
        
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("LiveCon 서버 관리")
        self.setGeometry(100, 100, 900, 700)
        
        # 중앙 위젯 및 레이아웃
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 탭 위젯 생성
        tab_widget = QTabWidget()
        
        # 서버 상태 탭
        server_tab = self.create_server_tab()
        tab_widget.addTab(server_tab, "서버 상태")
        
        # 센서 데이터 탭
        data_tab = self.create_data_tab()
        tab_widget.addTab(data_tab, "센서 데이터")
        
        # 로그 탭
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "로그")
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        central_widget.setLayout(main_layout)
        
        # 상태바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("서버 중지됨")
        
        # 타이머 설정 (UI 업데이트용)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # 1초마다 업데이트
        
    def create_server_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 서버 제어 그룹
        control_group = QGroupBox("서버 제어")
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("서버 시작")
        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn = QPushButton("서버 중지")
        self.stop_btn.clicked.connect(self.stop_server)
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_group.setLayout(control_layout)
        
        # 서버 정보 그룹
        info_group = QGroupBox("서버 정보")
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("서버 주소:"), 0, 0)
        info_layout.addWidget(QLabel("localhost:12347"), 0, 1)
        
        info_layout.addWidget(QLabel("서버 상태:"), 1, 0)
        self.status_label = QLabel("중지됨")
        info_layout.addWidget(self.status_label, 1, 1)
        
        info_layout.addWidget(QLabel("연결된 클라이언트:"), 2, 0)
        self.client_count_label = QLabel("0")
        info_layout.addWidget(self.client_count_label, 2, 1)
        
        info_layout.addWidget(QLabel("데이터베이스:"), 3, 0)
        self.db_status_label = QLabel("연결 확인 중...")
        info_layout.addWidget(self.db_status_label, 3, 1)
        
        info_group.setLayout(info_layout)
        
        # 연결된 클라이언트 목록
        clients_group = QGroupBox("연결된 클라이언트")
        clients_layout = QVBoxLayout()
        
        self.clients_list = QTextEdit()
        self.clients_list.setMaximumHeight(150)
        self.clients_list.setReadOnly(True)
        clients_layout.addWidget(self.clients_list)
        clients_group.setLayout(clients_layout)
        
        layout.addWidget(control_group)
        layout.addWidget(info_group)
        layout.addWidget(clients_group)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
        
    def create_data_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # 최근 데이터 테이블
        data_group = QGroupBox("최근 센서 데이터")
        data_layout = QVBoxLayout()
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(7)
        self.data_table.setHorizontalHeaderLabels([
            "시간", "클라이언트", "센서 ID", "온도(°C)", "용존산소(ppm)", 
            "수온(°C)", "위치"
        ])
        
        # 테이블 헤더가 창 크기에 맞게 자동 조절되도록 설정
        header = self.data_table.horizontalHeader()
        header.setStretchLastSection(True)  # 마지막 컬럼이 남은 공간을 채움
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 시간 컬럼
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # 클라이언트 컬럼
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 센서 ID 컬럼
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 온도 컬럼
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 용존산소 컬럼
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 수온 컬럼
        header.setSectionResizeMode(6, QHeaderView.Stretch)           # 위치 컬럼
        
        data_layout.addWidget(self.data_table)
        data_group.setLayout(data_layout)
        
        layout.addWidget(data_group)
        tab.setLayout(layout)
        return tab
        
    def create_log_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        log_group = QGroupBox("서버 로그")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        
        # 로그 제어 버튼
        log_control_layout = QHBoxLayout()
        clear_log_btn = QPushButton("로그 지우기")
        clear_log_btn.clicked.connect(self.clear_log)
        log_control_layout.addWidget(clear_log_btn)
        log_control_layout.addStretch()
        
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(log_control_layout)
        log_group.setLayout(log_layout)
        
        layout.addWidget(log_group)
        tab.setLayout(layout)
        return tab
        
    def start_server(self):
        if self.server_worker is None or not self.server_worker.isRunning():
            self.server_worker = ServerWorker(self.callback_handler)
            self.server_worker.server_started.connect(self.on_server_started)
            
            self.server_worker.start()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("시작 중...")
            self.status_bar.showMessage("서버 시작 중...")
    
    def on_server_started(self, success):
        if success:
            self.status_label.setText("실행 중")
            self.status_bar.showMessage("서버 실행 중")
            self.add_log("서버가 성공적으로 시작되었습니다")
        else:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("시작 실패")
            self.status_bar.showMessage("서버 시작 실패")
            
    def stop_server(self):
        if self.server_worker and self.server_worker.isRunning():
            self.server_worker.stop_server()
            self.server_worker.quit()
            self.server_worker.wait()
            
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("중지됨")
            self.status_bar.showMessage("서버 중지됨")
            self.connected_clients.clear()
            self.update_clients_display()
            
    def on_client_connected(self, client_addr):
        self.connected_clients.add(client_addr)
        self.update_clients_display()
        self.add_log(f"클라이언트 연결: {client_addr}")
        
    def on_client_disconnected(self, client_addr):
        self.connected_clients.discard(client_addr)
        self.update_clients_display()
        self.add_log(f"클라이언트 연결 해제: {client_addr}")
        
    def on_data_received(self, data, client_addr):
        # 테이블에 데이터 추가
        row_count = self.data_table.rowCount()
        self.data_table.insertRow(row_count)
        
        current_time = datetime.now().strftime("%H:%M:%S")
        location_str = f"{data['LOC'][0]:.4f}, {data['LOC'][1]:.4f}"
        
        items = [
            current_time,
            client_addr,
            str(data['ID']),
            f"{data['TEMP']:.1f}",
            f"{data['DO']:.2f}",
            f"{data['WTR_TEMP']:.1f}",
            location_str
        ]
        
        for col, item in enumerate(items):
            self.data_table.setItem(row_count, col, QTableWidgetItem(item))
            
        # 테이블을 최신 데이터가 보이도록 스크롤
        self.data_table.scrollToBottom()
        
        # 최대 100개 행만 유지
        if row_count > 100:
            self.data_table.removeRow(0)
            
    def update_clients_display(self):
        # 서버 워커에서 실제 연결된 클라이언트 목록을 가져옴
        if self.server_worker:
            current_clients = self.server_worker.get_connected_clients()
            self.connected_clients = set(current_clients)
        
        self.client_count_label.setText(str(len(self.connected_clients)))
        self.clients_list.clear()
        for client in self.connected_clients:
            self.clients_list.append(client)
            
    def add_log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.append(log_entry)
        
        # 로그를 최신으로 스크롤
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)
        
    def clear_log(self):
        self.log_text.clear()
        
    def update_status(self):
        # 데이터베이스 연결 상태 확인
        try:
            conn, cursor = connect_to_database()
            if conn and cursor:
                cursor.close()
                conn.close()
                self.db_status_label.setText("연결됨")
            else:
                self.db_status_label.setText("연결 실패")
        except:
            self.db_status_label.setText("연결 실패")
            
    def closeEvent(self, event):
        if self.server_worker and self.server_worker.isRunning():
            self.stop_server()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LiveConServerGUI()
    window.show()
    sys.exit(app.exec_())