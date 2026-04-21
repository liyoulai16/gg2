from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from enum import Enum
import json


class ThemeType(Enum):
    LIGHT = "light"
    DARK = "dark"
    CUSTOM = "custom"


class Currency:
    def __init__(self, code, symbol, name, rate=1.0):
        self.code = code
        self.symbol = symbol
        self.name = name
        self.rate = rate


CURRENCIES = {
    'CNY': Currency('CNY', '¥', '人民币', 1.0),
    'USD': Currency('USD', '$', '美元', 7.25),
    'EUR': Currency('EUR', '€', '欧元', 7.8),
    'GBP': Currency('GBP', '£', '英镑', 9.1),
    'JPY': Currency('JPY', '¥', '日元', 0.048),
    'HKD': Currency('HKD', 'HK$', '港币', 0.93),
}


class ThemeColors:
    LIGHT = {
        'window': QColor(250, 250, 250),
        'window_text': QColor(50, 50, 50),
        'base': QColor(255, 255, 255),
        'alternate_base': QColor(245, 245, 245),
        'text': QColor(50, 50, 50),
        'button': QColor(240, 240, 240),
        'button_text': QColor(50, 50, 50),
        'highlight': QColor(66, 133, 244),
        'highlight_text': QColor(255, 255, 255),
        'bright_text': QColor(255, 255, 255),
        'tooltip_base': QColor(255, 255, 255),
        'tooltip_text': QColor(50, 50, 50),
        'header_bg': QColor(66, 133, 244),
        'tab_hover': QColor(232, 232, 232),
        'tab_selected': QColor(255, 255, 255),
        'success': QColor(52, 168, 83),
        'danger': QColor(234, 67, 53),
    }

    DARK = {
        'window': QColor(32, 33, 36),
        'window_text': QColor(232, 234, 237),
        'base': QColor(41, 42, 45),
        'alternate_base': QColor(48, 49, 52),
        'text': QColor(232, 234, 237),
        'button': QColor(60, 64, 67),
        'button_text': QColor(232, 234, 237),
        'highlight': QColor(138, 180, 248),
        'highlight_text': QColor(32, 33, 36),
        'bright_text': QColor(255, 255, 255),
        'tooltip_base': QColor(48, 49, 52),
        'tooltip_text': QColor(232, 234, 237),
        'header_bg': QColor(138, 180, 248),
        'tab_hover': QColor(80, 85, 88),
        'tab_selected': QColor(60, 64, 67),
        'success': QColor(82, 196, 113),
        'danger': QColor(246, 97, 81),
    }


class SettingsManager(QObject):
    theme_changed = pyqtSignal()
    currency_changed = pyqtSignal()
    format_changed = pyqtSignal()
    layout_changed = pyqtSignal()

    DEFAULT_SETTINGS = {
        'theme': 'light',
        'custom_theme_colors': {},
        'currency_code': 'CNY',
        'show_currency_symbol': True,
        'decimal_places': 2,
        'date_format': 'yyyy-MM-dd',
        'tab_order': ['transaction', 'account', 'category', 'statistics', 'budget', 'debt', 'recurring', 'trash'],
        'highlight_tabs': [],
        'highlight_color': '#ff9800',
    }

    TAB_LABELS = {
        'transaction': '💰 收支记录',
        'account': '💳 账户管理',
        'category': '📁 分类管理',
        'statistics': '📊 统计分析',
        'budget': '💰 预算管理',
        'debt': '💸 债务管理',
        'recurring': '🔄 周期性账单',
        'trash': '🗑️ 回收站',
    }

    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self._settings = {}
        self._load_settings()

    def _load_settings(self):
        if self.db:
            for key, default_value in self.DEFAULT_SETTINGS.items():
                stored_value = self.db.get_app_setting(key)
                if stored_value is not None:
                    try:
                        if key in ['custom_theme_colors', 'tab_order', 'highlight_tabs']:
                            self._settings[key] = json.loads(stored_value)
                        elif key == 'decimal_places':
                            self._settings[key] = int(stored_value)
                        elif key == 'show_currency_symbol':
                            self._settings[key] = stored_value.lower() in ['true', '1', 'yes']
                        else:
                            self._settings[key] = stored_value
                    except (json.JSONDecodeError, ValueError):
                        self._settings[key] = default_value
                else:
                    self._settings[key] = default_value
        else:
            self._settings = self.DEFAULT_SETTINGS.copy()

    def _save_setting(self, key, value):
        self._settings[key] = value
        if self.db:
            if isinstance(value, (dict, list)):
                self.db.set_app_setting(key, json.dumps(value))
            elif isinstance(value, bool):
                self.db.set_app_setting(key, 'true' if value else 'false')
            else:
                self.db.set_app_setting(key, str(value))

    def get_theme(self):
        return self._settings.get('theme', 'light')

    def set_theme(self, theme):
        if theme in ['light', 'dark', 'custom']:
            self._save_setting('theme', theme)
            self.theme_changed.emit()

    def get_custom_theme_colors(self):
        return self._settings.get('custom_theme_colors', {})

    def set_custom_theme_colors(self, colors):
        self._save_setting('custom_theme_colors', colors)
        self.theme_changed.emit()

    def get_theme_colors(self):
        theme = self.get_theme()
        if theme == 'dark':
            return ThemeColors.DARK.copy()
        elif theme == 'custom':
            custom = self.get_custom_theme_colors()
            colors = ThemeColors.LIGHT.copy()
            for key, value in custom.items():
                if key in colors and value:
                    colors[key] = QColor(value) if isinstance(value, str) else QColor(*value)
            return colors
        return ThemeColors.LIGHT.copy()

    def get_currency_code(self):
        return self._settings.get('currency_code', 'CNY')

    def set_currency_code(self, code):
        if code in CURRENCIES:
            self._save_setting('currency_code', code)
            self.currency_changed.emit()

    def get_currency(self):
        code = self.get_currency_code()
        return CURRENCIES.get(code, CURRENCIES['CNY'])

    def get_all_currencies(self):
        return CURRENCIES.copy()

    def convert_amount(self, amount, from_currency='CNY', to_currency=None):
        if to_currency is None:
            to_currency = self.get_currency_code()
        
        if from_currency == to_currency:
            return amount
        
        from_rate = CURRENCIES[from_currency].rate if from_currency in CURRENCIES else 1.0
        to_rate = CURRENCIES[to_currency].rate if to_currency in CURRENCIES else 1.0
        
        amount_in_cny = amount * from_rate
        converted_amount = amount_in_cny / to_rate
        
        return round(converted_amount, self.get_decimal_places())

    def format_amount(self, amount, currency_code=None):
        if currency_code is None:
            currency_code = self.get_currency_code()
        
        currency = CURRENCIES.get(currency_code, CURRENCIES['CNY'])
        decimal_places = self.get_decimal_places()
        show_symbol = self._settings.get('show_currency_symbol', True)
        
        formatted = f"{amount:,.{decimal_places}f}"
        
        if show_symbol:
            formatted = f"{currency.symbol} {formatted}"
        
        return formatted

    def get_decimal_places(self):
        return self._settings.get('decimal_places', 2)

    def set_decimal_places(self, places):
        if 0 <= places <= 6:
            self._save_setting('decimal_places', places)
            self.format_changed.emit()

    def get_date_format(self):
        return self._settings.get('date_format', 'yyyy-MM-dd')

    def set_date_format(self, format_str):
        valid_formats = ['yyyy-MM-dd', 'yyyy/MM/dd', 'MM/dd/yyyy', 'dd/MM/yyyy', 'yyyy年MM月dd日']
        if format_str in valid_formats:
            self._save_setting('date_format', format_str)
            self.format_changed.emit()

    def get_show_currency_symbol(self):
        return self._settings.get('show_currency_symbol', True)

    def set_show_currency_symbol(self, show):
        self._save_setting('show_currency_symbol', show)
        self.format_changed.emit()

    def get_tab_order(self):
        default_order = self.DEFAULT_SETTINGS['tab_order']
        order = self._settings.get('tab_order', default_order)
        existing_tabs = [t for t in order if t in self.TAB_LABELS]
        for tab in default_order:
            if tab not in existing_tabs:
                existing_tabs.append(tab)
        return existing_tabs

    def set_tab_order(self, order):
        if isinstance(order, list) and len(order) == len(self.TAB_LABELS):
            self._save_setting('tab_order', order)
            self.layout_changed.emit()

    def get_highlight_tabs(self):
        return self._settings.get('highlight_tabs', [])

    def set_highlight_tabs(self, tabs):
        if isinstance(tabs, list):
            self._save_setting('highlight_tabs', tabs)
            self.layout_changed.emit()

    def get_highlight_color(self):
        return self._settings.get('highlight_color', '#ff9800')

    def set_highlight_color(self, color):
        self._save_setting('highlight_color', color)
        self.layout_changed.emit()

    def get_tab_label(self, tab_key):
        return self.TAB_LABELS.get(tab_key, tab_key)

    def apply_palette(self, app):
        colors = self.get_theme_colors()
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, colors['window'])
        palette.setColor(QPalette.ColorRole.WindowText, colors['window_text'])
        palette.setColor(QPalette.ColorRole.Base, colors['base'])
        palette.setColor(QPalette.ColorRole.AlternateBase, colors['alternate_base'])
        palette.setColor(QPalette.ColorRole.ToolTipBase, colors['tooltip_base'])
        palette.setColor(QPalette.ColorRole.ToolTipText, colors['tooltip_text'])
        palette.setColor(QPalette.ColorRole.Text, colors['text'])
        palette.setColor(QPalette.ColorRole.Button, colors['button'])
        palette.setColor(QPalette.ColorRole.ButtonText, colors['button_text'])
        palette.setColor(QPalette.ColorRole.BrightText, colors['bright_text'])
        palette.setColor(QPalette.ColorRole.Highlight, colors['highlight'])
        palette.setColor(QPalette.ColorRole.HighlightedText, colors['highlight_text'])
        
        app.setPalette(palette)

    def get_stylesheet(self):
        theme = self.get_theme()
        colors = self.get_theme_colors()
        
        if theme == 'dark':
            return self._get_dark_stylesheet(colors)
        elif theme == 'custom':
            return self._get_custom_stylesheet(colors)
        return self._get_light_stylesheet(colors)

    def _get_light_stylesheet(self, colors):
        return """
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
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
                padding: 8px;
            }
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
                background-color: #e8e8e0;
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
            QScrollBar:vertical {
                border: none;
                background-color: #f5f5f5;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdbdbd;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9e9e9e;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                border: none;
                background-color: #f5f5f5;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #bdbdbd;
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #9e9e9e;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QToolTip {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                color: #5f6368;
            }
        """

    def _get_dark_stylesheet(self, colors):
        header_color = colors['header_bg'].name()
        highlight_color = colors['highlight'].name()
        tab_hover = colors['tab_hover'].name()
        tab_selected = colors['tab_selected'].name()
        success_color = colors['success'].name()
        danger_color = colors['danger'].name()
        
        return f"""
            QMainWindow {{
                background-color: #202124;
            }}
            QTabWidget::pane {{
                border: 1px solid #5f6368;
                background-color: #28292c;
                border-radius: 4px;
            }}
            QTabBar::tab {{
                background-color: #323639;
                border: 1px solid #5f6368;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 12px 24px;
                margin-right: 2px;
                font-size: 14px;
                color: #e8eaed;
            }}
            QTabBar::tab:selected {{
                background-color: {tab_selected};
                border-bottom: 2px solid {highlight_color};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {tab_hover};
            }}
            QPushButton {{
                background-color: {highlight_color};
                color: #202124;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #aecbfa;
            }}
            QPushButton:pressed {{
                background-color: #8ab4f8;
            }}
            QPushButton:disabled {{
                background-color: #5f6368;
                color: #9aa0a6;
            }}
            QPushButton[class="danger"] {{
                background-color: {danger_color};
                color: white;
            }}
            QPushButton[class="danger"]:hover {{
                background-color: #f28b82;
            }}
            QPushButton[class="success"] {{
                background-color: {success_color};
                color: #202124;
            }}
            QPushButton[class="success"]:hover {{
                background-color: #81c995;
            }}
            QLineEdit, QTextEdit, QComboBox, QDateEdit {{
                padding: 10px;
                border: 1px solid #5f6368;
                border-radius: 4px;
                font-size: 13px;
                background-color: #28292c;
                color: #e8eaed;
            }}
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid {highlight_color};
            }}
            QSpinBox, QDoubleSpinBox {{
                padding: 10px;
                border: 1px solid #5f6368;
                border-radius: 4px;
                font-size: 13px;
                background-color: #28292c;
                color: #e8eaed;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {highlight_color};
            }}
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                width: 0px;
                border: none;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                width: 0px;
                border: none;
            }}
            QTableWidget {{
                border: 1px solid #5f6368;
                border-radius: 4px;
                gridline-color: #3c4043;
                background-color: #28292c;
                selection-background-color: {highlight_color};
                selection-color: #202124;
                color: #e8eaed;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: #3c4043;
                padding: 12px;
                border: none;
                border-bottom: 1px solid #5f6368;
                font-weight: bold;
                color: #e8eaed;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid #5f6368;
                border-radius: 4px;
                margin-top: 16px;
                padding-top: 16px;
                color: #e8eaed;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #e8eaed;
            }}
            QRadioButton {{
                spacing: 8px;
                color: #e8eaed;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox {{
                spacing: 8px;
                color: #e8eaed;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QStatusBar {{
                background-color: #3c4043;
                border-top: 1px solid #5f6368;
                padding: 8px;
                color: #e8eaed;
            }}
            QMenuBar {{
                background-color: #3c4043;
                padding: 2px;
                border-bottom: 1px solid #5f6368;
                color: #e8eaed;
            }}
            QMenuBar::item {{
                padding: 5px 12px;
                border-radius: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: #5f6368;
            }}
            QMenu {{
                background-color: #28292c;
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 25px;
                border-radius: 4px;
                color: #e8eaed;
            }}
            QMenu::item:selected {{
                background-color: #5f6368;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: #5f6368;
                margin: 5px 10px;
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: #3c4043;
                width: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #5f6368;
                border-radius: 6px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #70757a;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                border: none;
                background-color: #3c4043;
                height: 12px;
                border-radius: 6px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: #5f6368;
                border-radius: 6px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: #70757a;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QToolTip {{
                background-color: #28292c;
                border: 1px solid #5f6368;
                border-radius: 4px;
                padding: 8px;
                color: #e8eaed;
            }}
            QComboBox QAbstractItemView {{
                background-color: #28292c;
                color: #e8eaed;
                selection-background-color: #5f6368;
            }}
            QCalendarWidget QWidget {{
                alternate-background-color: #3c4043;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                background-color: #28292c;
                color: #e8eaed;
                selection-background-color: {highlight_color};
                selection-color: #202124;
            }}
        """

    def _get_custom_stylesheet(self, colors):
        theme = self.get_theme()
        if theme == 'custom':
            custom_colors = self.get_custom_theme_colors()
            base_colors = ThemeColors.LIGHT.copy()
            for key, value in custom_colors.items():
                if key in base_colors and value:
                    base_colors[key] = QColor(value) if isinstance(value, str) else QColor(*value)
            
            header_color = base_colors.get('header_bg', QColor(66, 133, 244)).name()
            highlight_color = base_colors.get('highlight', QColor(66, 133, 244)).name()
            success_color = base_colors.get('success', QColor(52, 168, 83)).name()
            danger_color = base_colors.get('danger', QColor(234, 67, 53)).name()
            
            return f"""
                QPushButton {{
                    background-color: {highlight_color};
                }}
                QTabBar::tab:selected {{
                    border-bottom: 2px solid {highlight_color};
                }}
                QPushButton[class="danger"] {{
                    background-color: {danger_color};
                }}
                QPushButton[class="success"] {{
                    background-color: {success_color};
                }}
                QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus,
                QSpinBox:focus, QDoubleSpinBox:focus {{
                    border: 2px solid {highlight_color};
                }}
            """
        return ""


_settings_instance = None


def get_settings(db=None):
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager(db)
    return _settings_instance
