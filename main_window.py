from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPalette
from database import Database
from widgets import TransactionWidget, AccountWidget, CategoryWidget, StatisticsWidget, BudgetWidget, DebtWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('记账应用')
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self.setup_style()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = self.create_header()
        main_layout.addWidget(header)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(False)

        self.transaction_widget = TransactionWidget(self.db)
        self.account_widget = AccountWidget(self.db)
        self.category_widget = CategoryWidget(self.db)
        self.statistics_widget = StatisticsWidget(self.db)
        self.budget_widget = BudgetWidget(self.db)
        self.debt_widget = DebtWidget(self.db)

        self.tab_widget.addTab(self.transaction_widget, '💰 收支记录')
        self.tab_widget.addTab(self.account_widget, '💳 账户管理')
        self.tab_widget.addTab(self.category_widget, '📁 分类管理')
        self.tab_widget.addTab(self.statistics_widget, '📊 统计分析')
        self.tab_widget.addTab(self.budget_widget, '💰 预算管理')
        self.tab_widget.addTab(self.debt_widget, '💸 债务管理')

        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

        self.status_bar = self.statusBar()
        self.update_status_bar()

    def setup_style(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(250, 250, 250))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.Text, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(66, 133, 244))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #fafafa;
            }
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 12px 24px;
                margin-right: 2px;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4285f4;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e8e8e8;
            }
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
            QPushButton:pressed {
                background-color: #2851a3;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
            QPushButton[class="danger"] {
                background-color: #ea4335;
            }
            QPushButton[class="danger"]:hover {
                background-color: #d33427;
            }
            QPushButton[class="success"] {
                background-color: #34a853;
            }
            QPushButton[class="success"]:hover {
                background-color: #2d8e47;
            }
            QLineEdit, QTextEdit, QComboBox, QDateEdit {
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
                border: 2px solid #4285f4;
            }
            QSpinBox, QDoubleSpinBox {
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #4285f4;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                width: 0px;
                border: none;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                width: 0px;
                border: none;
            }
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                gridline-color: #f0f0f0;
                background-color: white;
                selection-background-color: #e8f0fe;
                selection-color: #202124;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 12px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                font-weight: bold;
                color: #5f6368;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                margin-top: 16px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #5f6368;
            }
            QRadioButton {
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
            }
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
                padding: 8px;
            }
        """)

    def create_header(self):
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #4285f4;")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        title_label = QLabel('📊 个人记账应用')
        title_label.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")

        total_balance = self.db.get_total_balance()
        balance_label = QLabel(f'总资产: ¥ {total_balance:,.2f}')
        balance_label.setStyleSheet("color: white; font-size: 16px;")

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(balance_label)

        return header

    def on_tab_changed(self, index):
        if index == 0:
            self.transaction_widget.refresh_data()
        elif index == 1:
            self.account_widget.refresh_data()
        elif index == 2:
            self.category_widget.refresh_data()
        elif index == 3:
            self.statistics_widget.refresh_data()
        elif index == 4:
            self.budget_widget.refresh_data()
        elif index == 5:
            self.debt_widget.refresh_data()

    def update_status_bar(self):
        total_balance = self.db.get_total_balance()
        accounts = self.db.get_all_accounts()
        self.status_bar.showMessage(f'账户数: {len(accounts)} | 总资产: ¥ {total_balance:,.2f}')

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出记账应用吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
