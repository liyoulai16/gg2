from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QMessageBox, QApplication,
    QPushButton, QMenuBar, QMenu, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QAction
from database import Database
from widgets import (
    TransactionWidget, AccountWidget, CategoryWidget, 
    StatisticsWidget, BudgetWidget, DebtWidget, RecurringWidget,
    ExportDialog, ImportDialog, BackupRestoreDialog
)
from widgets.quick_entry_widget import QuickEntryWidget
from global_hotkey import HotkeyManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.quick_entry_window = None
        self.hotkey_manager = None
        self.init_ui()
        self.init_quick_entry()
        self.init_hotkey()

    def init_ui(self):
        self.setWindowTitle('记账应用')
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self.setup_style()
        self.create_menu_bar()

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
        self.recurring_widget = RecurringWidget(self.db)

        self.tab_widget.addTab(self.transaction_widget, '💰 收支记录')
        self.tab_widget.addTab(self.account_widget, '💳 账户管理')
        self.tab_widget.addTab(self.category_widget, '📁 分类管理')
        self.tab_widget.addTab(self.statistics_widget, '📊 统计分析')
        self.tab_widget.addTab(self.budget_widget, '💰 预算管理')
        self.tab_widget.addTab(self.debt_widget, '💸 债务管理')
        self.tab_widget.addTab(self.recurring_widget, '🔄 周期性账单')

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

        quick_entry_btn = QPushButton('⚡ 快速记账 (Alt+Ctrl+J)')
        quick_entry_btn.setMinimumHeight(40)
        quick_entry_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        quick_entry_btn.clicked.connect(self.show_quick_entry)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(quick_entry_btn)
        layout.addSpacing(20)
        layout.addWidget(balance_label)

        return header

    def init_quick_entry(self):
        self.quick_entry_window = QuickEntryWidget(self.db)

    def init_hotkey(self):
        self.hotkey_manager = HotkeyManager(self)
        if self.hotkey_manager.is_available():
            if self.hotkey_manager.setup_default_hotkey():
                self.hotkey_manager.connect_activated(self.show_quick_entry)
            else:
                print("警告: 全局快捷键注册失败，可能已被其他程序占用")
        else:
            print("警告: 当前系统不支持全局快捷键")

    def show_quick_entry(self):
        if self.quick_entry_window:
            self.quick_entry_window.load_presets()
            
            screen = QApplication.primaryScreen()
            screen_geometry = screen.availableGeometry()
            
            window_geometry = self.quick_entry_window.frameGeometry()
            x = (screen_geometry.width() - window_geometry.width()) // 2
            y = (screen_geometry.height() - window_geometry.height()) // 2
            
            self.quick_entry_window.move(x, y)
            self.quick_entry_window.show()
            self.quick_entry_window.raise_()
            self.quick_entry_window.activateWindow()

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
        elif index == 6:
            self.recurring_widget.refresh_data()

    def update_status_bar(self):
        total_balance = self.db.get_total_balance()
        accounts = self.db.get_all_accounts()
        self.status_bar.showMessage(f'账户数: {len(accounts)} | 总资产: ¥ {total_balance:,.2f}')

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #f5f5f5;
                padding: 2px;
                border-bottom: 1px solid #e0e0e0;
            }
            QMenuBar::item {
                padding: 5px 12px;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #e8e8e8;
            }
            QMenu {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e8f0fe;
            }
            QMenu::separator {
                height: 1px;
                background-color: #e0e0e0;
                margin: 5px 10px;
            }
        """)

        file_menu = menubar.addMenu('文件(&F)')

        export_action = QAction('📤 导出数据...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.show_export_dialog)
        file_menu.addAction(export_action)

        import_action = QAction('📥 导入数据...', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)

        file_menu.addSeparator()

        backup_action = QAction('💾 数据备份与恢复...', self)
        backup_action.triggered.connect(self.show_backup_dialog)
        file_menu.addAction(backup_action)

        file_menu.addSeparator()

        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_export_dialog(self):
        dialog = ExportDialog(self.db, self)
        dialog.exec()
        self.refresh_all_widgets()

    def show_import_dialog(self):
        dialog = ImportDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_all_widgets()

    def show_backup_dialog(self):
        dialog = BackupRestoreDialog(self.db, self)
        dialog.exec()

    def show_about(self):
        QMessageBox.about(
            self, '关于记账应用',
            '📊 个人记账应用\n\n'
            '版本: 1.0.0\n\n'
            '功能特性:\n'
            '• 收支记录管理\n'
            '• 多账户管理\n'
            '• 分类管理\n'
            '• 统计分析\n'
            '• 预算管理\n'
            '• 债务管理\n'
            '• 周期性账单\n'
            '• 数据导入导出\n'
            '• 数据库备份恢复'
        )

    def refresh_all_widgets(self):
        self.transaction_widget.refresh_data()
        self.account_widget.refresh_data()
        self.category_widget.refresh_data()
        self.statistics_widget.refresh_data()
        self.budget_widget.refresh_data()
        self.debt_widget.refresh_data()
        self.recurring_widget.refresh_data()
        self.update_status_bar()

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出记账应用吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.hotkey_manager:
                self.hotkey_manager.cleanup()
            if self.quick_entry_window:
                self.quick_entry_window.close()
            event.accept()
        else:
            event.ignore()
