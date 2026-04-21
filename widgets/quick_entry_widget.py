from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QMessageBox, QDoubleSpinBox, QFrame, QSizePolicy,
    QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QFont, QKeyEvent
from datetime import datetime


class QuickEntryWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.last_amount = ''
        self.init_ui()
        self.load_presets()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        
        self.setFixedSize(380, 340)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        
        title_label = QLabel('⚡ 快速记账')
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        close_btn = QPushButton('✕')
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        
        container_layout.addLayout(header_layout)
        
        type_layout = QHBoxLayout()
        type_layout.setSpacing(20)
        
        self.type_group = QButtonGroup(self)
        self.income_radio = QRadioButton('💰 收入')
        self.expense_radio = QRadioButton('💸 支出')
        self.expense_radio.setChecked(True)
        self.type_group.addButton(self.income_radio)
        self.type_group.addButton(self.expense_radio)
        
        for radio in [self.income_radio, self.expense_radio]:
            radio.setStyleSheet("""
                QRadioButton {
                    font-size: 15px;
                    font-weight: bold;
                    spacing: 8px;
                    padding: 8px;
                }
                QRadioButton::indicator {
                    width: 20px;
                    height: 20px;
                }
            """)
        
        self.income_radio.toggled.connect(self.on_type_changed)
        
        type_layout.addWidget(self.income_radio)
        type_layout.addWidget(self.expense_radio)
        type_layout.addStretch()
        
        container_layout.addLayout(type_layout)
        
        amount_layout = QVBoxLayout()
        amount_layout.setSpacing(8)
        
        amount_label = QLabel('金额')
        amount_label.setStyleSheet("font-size: 13px; color: #666; font-weight: bold;")
        amount_layout.addWidget(amount_label)
        
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix('¥ ')
        self.amount_spin.setValue(0)
        self.amount_spin.setMinimumHeight(70)
        self.amount_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.amount_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.amount_spin.setStyleSheet("""
            QDoubleSpinBox {
                font-size: 32px;
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 10px;
                background-color: #fafafa;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #4285f4;
                background-color: white;
            }
        """)
        amount_layout.addWidget(self.amount_spin)
        
        container_layout.addLayout(amount_layout)
        
        self.preset_info_label = QLabel('')
        self.preset_info_label.setStyleSheet("""
            font-size: 12px;
            color: #888;
            padding: 8px;
            background-color: #f8f9fa;
            border-radius: 6px;
        """)
        self.preset_info_label.setWordWrap(True)
        container_layout.addWidget(self.preset_info_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        settings_btn = QPushButton('⚙ 预设')
        settings_btn.setMinimumHeight(45)
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                color: #666;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        settings_btn.clicked.connect(self.open_preset_settings)
        btn_layout.addWidget(settings_btn)
        
        submit_btn = QPushButton('✓ 确认记账')
        submit_btn.setMinimumHeight(45)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
            QPushButton:pressed {
                background-color: #2851a3;
            }
        """)
        submit_btn.clicked.connect(self.submit_transaction)
        btn_layout.addWidget(submit_btn, 2)
        
        container_layout.addLayout(btn_layout)
        
        main_layout.addWidget(self.container)
        
        self.drag_position = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.submit_transaction()
        elif event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self.amount_spin.setFocus)
        self.amount_spin.selectAll()
        self.load_presets()

    def load_presets(self):
        type_ = 'income' if self.income_radio.isChecked() else 'expense'
        preset = self.db.get_default_quick_entry_preset(type_)
        
        if preset:
            self.current_preset = preset
            self.preset_info_label.setText(
                f"预设: {preset['name']} | 账户: {preset['account_name']} | 分类: {preset['category_name']}"
            )
        else:
            accounts = self.db.get_all_accounts()
            categories = self.db.get_all_categories(type_)
            
            if accounts and categories:
                self.current_preset = {
                    'account_id': accounts[0]['id'],
                    'account_name': accounts[0]['name'],
                    'category_id': categories[0]['id'],
                    'category_name': categories[0]['name'],
                    'description': ''
                }
                self.preset_info_label.setText(
                    f"使用默认值 | 账户: {accounts[0]['name']} | 分类: {categories[0]['name']}"
                )
            else:
                self.current_preset = None
                self.preset_info_label.setText("请先在主程序中添加账户和分类")

    def on_type_changed(self):
        self.load_presets()

    def submit_transaction(self):
        if not self.current_preset:
            QMessageBox.warning(self, '警告', '请先在主程序中添加账户和分类！')
            return
        
        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, '警告', '请输入有效的金额！')
            return
        
        type_ = 'income' if self.income_radio.isChecked() else 'expense'
        account_id = self.current_preset['account_id']
        category_id = self.current_preset['category_id']
        description = self.current_preset.get('description', '')
        date = datetime.now().strftime('%Y-%m-%d')
        
        if self.db.add_transaction(account_id, category_id, type_, amount, description, date):
            self.amount_spin.setValue(0)
            self.hide()
            
            main_window = self.find_main_window()
            if main_window:
                main_window.update_status_bar()
        else:
            QMessageBox.critical(self, '错误', '记账失败！')

    def find_main_window(self):
        for widget in QApplication.instance().topLevelWidgets():
            if widget.__class__.__name__ == 'MainWindow':
                return widget
        return None

    def open_preset_settings(self):
        from widgets.quick_entry_settings import QuickEntrySettingsDialog
        dialog = QuickEntrySettingsDialog(self.db, self)
        if dialog.exec():
            self.load_presets()
