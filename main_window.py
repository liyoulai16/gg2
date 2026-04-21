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
    ExportDialog, ImportDialog, BackupRestoreDialog, SettingsDialog
)
from widgets.quick_entry_widget import QuickEntryWidget
from global_hotkey import HotkeyManager
from settings import SettingsManager, get_settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.settings = get_settings(self.db)
        self.quick_entry_window = None
        self.hotkey_manager = None
        self._widget_map = {}
        self._tab_keys = []
        self.init_ui()
        self.init_quick_entry()
        self.init_hotkey()
        self.connect_settings_signals()

    def connect_settings_signals(self):
        self.settings.theme_changed.connect(self.on_theme_changed)
        self.settings.currency_changed.connect(self.on_currency_changed)
        self.settings.format_changed.connect(self.on_format_changed)
        self.settings.layout_changed.connect(self.on_layout_changed)

    def init_ui(self):
        self.setWindowTitle('记账应用')
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self.setup_style_from_settings()
        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = self.create_header()
        main_layout.addWidget(self.header)

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

        self._widget_map = {
            'transaction': self.transaction_widget,
            'account': self.account_widget,
            'category': self.category_widget,
            'statistics': self.statistics_widget,
            'budget': self.budget_widget,
            'debt': self.debt_widget,
            'recurring': self.recurring_widget,
        }

        self.setup_tabs_from_settings()

        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        main_layout.addWidget(self.tab_widget)

        self.status_bar = self.statusBar()
        self.update_status_bar()

    def setup_tabs_from_settings(self):
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        tab_order = self.settings.get_tab_order()
        highlight_tabs = self.settings.get_highlight_tabs()
        highlight_color = self.settings.get_highlight_color()
        
        self._tab_keys = []
        for tab_key in tab_order:
            if tab_key in self._widget_map:
                widget = self._widget_map[tab_key]
                label = self.settings.get_tab_label(tab_key)
                index = self.tab_widget.addTab(widget, label)
                self._tab_keys.append(tab_key)
                
                if tab_key in highlight_tabs:
                    self.tab_widget.tabBar().setTabTextColor(index, QColor(highlight_color))

    def setup_style_from_settings(self):
        app = QApplication.instance()
        self.settings.apply_palette(app)
        
        base_stylesheet = self.settings.get_stylesheet()
        self.setStyleSheet(base_stylesheet)

    def on_theme_changed(self):
        self.setup_style_from_settings()
        self.update_header_style()

    def on_currency_changed(self):
        self.update_status_bar()
        self.update_header_balance()
        self.refresh_all_widgets()

    def on_format_changed(self):
        self.update_status_bar()
        self.update_header_balance()
        self.refresh_all_widgets()

    def on_layout_changed(self):
        self.setup_tabs_from_settings()

    def update_header_style(self):
        colors = self.settings.get_theme_colors()
        header_color = colors.get('header_bg', QColor(66, 133, 244)).name()
        
        if self.settings.get_theme() == 'dark':
            text_color = '#202124'
        else:
            text_color = 'white'
        
        self.header.setStyleSheet(f"background-color: {header_color};")
        
        for i in range(self.header.layout().count()):
            item = self.header.layout().itemAt(i)
            if item.widget():
                widget = item.widget()
                if isinstance(widget, QLabel) and widget not in [self.header.layout().itemAt(self.header.layout().count() - 1).widget() if self.header.layout().count() > 0 else None]:
                    if '总资产' in widget.text():
                        widget.setStyleSheet(f"color: {text_color}; font-size: 16px;")
                    else:
                        widget.setStyleSheet(f"color: {text_color}; font-size: 22px; font-weight: bold;")

    def create_header(self):
        header = QWidget()
        header.setFixedHeight(80)
        colors = self.settings.get_theme_colors()
        header_color = colors.get('header_bg', QColor(66, 133, 244)).name()
        
        if self.settings.get_theme() == 'dark':
            text_color = '#202124'
        else:
            text_color = 'white'
        
        header.setStyleSheet(f"background-color: {header_color};")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        title_label = QLabel('📊 个人记账应用')
        title_label.setStyleSheet(f"color: {text_color}; font-size: 22px; font-weight: bold;")

        self.balance_label = QLabel()
        self.update_header_balance()
        self.balance_label.setStyleSheet(f"color: {text_color}; font-size: 16px;")

        quick_entry_btn = QPushButton('⚡ 快速记账 (Alt+Ctrl+J)')
        quick_entry_btn.setMinimumHeight(40)
        quick_entry_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.2);
                color: {text_color};
                border: 2px solid rgba(255, 255, 255, 0.5);
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.3);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.4);
            }}
        """)
        quick_entry_btn.clicked.connect(self.show_quick_entry)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(quick_entry_btn)
        layout.addSpacing(20)
        layout.addWidget(self.balance_label)

        return header

    def update_header_balance(self):
        total_balance = self.db.get_total_balance()
        formatted_balance = self.settings.format_amount(total_balance)
        if self.balance_label:
            self.balance_label.setText(f'总资产: {formatted_balance}')

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

    def show_settings_dialog(self):
        dialog = SettingsDialog(self.settings, self)
        dialog.settings_applied.connect(self.on_settings_applied)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.on_settings_applied()

    def on_settings_applied(self):
        self.setup_style_from_settings()
        self.update_header_style()
        self.setup_tabs_from_settings()
        self.update_status_bar()
        self.update_header_balance()
        self.refresh_all_widgets()

    def on_tab_changed(self, index):
        if 0 <= index < len(self._tab_keys):
            tab_key = self._tab_keys[index]
            if tab_key == 'transaction':
                self.transaction_widget.refresh_data()
            elif tab_key == 'account':
                self.account_widget.refresh_data()
            elif tab_key == 'category':
                self.category_widget.refresh_data()
            elif tab_key == 'statistics':
                self.statistics_widget.refresh_data()
            elif tab_key == 'budget':
                self.budget_widget.refresh_data()
            elif tab_key == 'debt':
                self.debt_widget.refresh_data()
            elif tab_key == 'recurring':
                self.recurring_widget.refresh_data()

    def update_status_bar(self):
        total_balance = self.db.get_total_balance()
        accounts = self.db.get_all_accounts()
        formatted_balance = self.settings.format_amount(total_balance)
        self.status_bar.showMessage(f'账户数: {len(accounts)} | 总资产: {formatted_balance}')

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        theme = self.settings.get_theme()
        if theme == 'dark':
            menubar_bg = '#3c4043'
            menubar_border = '#5f6368'
            menubar_selected = '#5f6368'
            menu_bg = '#28292c'
            menu_border = '#5f6368'
            menu_selected = '#5f6368'
            separator_color = '#5f6368'
        else:
            menubar_bg = '#f5f5f5'
            menubar_border = '#e0e0e0'
            menubar_selected = '#e8e8e8'
            menu_bg = 'white'
            menu_border = '#e0e0e0'
            menu_selected = '#e8f0fe'
            separator_color = '#e0e0e0'
        
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {menubar_bg};
                padding: 2px;
                border-bottom: 1px solid {menubar_border};
            }}
            QMenuBar::item {{
                padding: 5px 12px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {menubar_selected};
            }}
            QMenu {{
                background-color: {menu_bg};
                border: 1px solid {menu_border};
                border-radius: 4px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 25px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {menu_selected};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {separator_color};
                margin: 5px 10px;
            }}
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

        edit_menu = menubar.addMenu('编辑(&E)')
        
        settings_action = QAction('⚙️ 设置...', self)
        settings_action.setShortcut('Ctrl+,')
        settings_action.triggered.connect(self.show_settings_dialog)
        edit_menu.addAction(settings_action)

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
            '• 数据库备份恢复\n'
            '• 个性化主题设置\n'
            '• 货币单位切换\n'
            '• 界面布局自定义'
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
