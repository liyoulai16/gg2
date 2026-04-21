from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QRadioButton, QButtonGroup, QComboBox, QSpinBox,
    QCheckBox, QColorDialog, QListWidget, QListWidgetItem,
    QTabWidget, QWidget, QFrame, QMessageBox, QDoubleSpinBox,
    QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings import SettingsManager, CURRENCIES, get_settings


class ThemePreviewWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        self._theme = 'light'
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        self.header = QFrame()
        self.header.setFixedWidth(60)
        self.header.setStyleSheet("""
            QFrame {
                background-color: #4285f4;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.header)
        
        self.content = QFrame()
        self.content.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.content, 1)

    def set_theme(self, theme, colors=None):
        self._theme = theme
        if theme == 'dark':
            self.setStyleSheet("""
                QFrame {
                    background-color: #202124;
                    border: 2px solid #5f6368;
                    border-radius: 8px;
                }
            """)
            self.header.setStyleSheet("""
                QFrame {
                    background-color: #8ab4f8;
                    border-radius: 4px;
                }
            """)
            self.content.setStyleSheet("""
                QFrame {
                    background-color: #28292c;
                    border-radius: 4px;
                }
            """)
        elif colors and theme == 'custom':
            header_color = colors.get('header_bg', '#4285f4')
            if isinstance(header_color, QColor):
                header_color = header_color.name()
            window_color = colors.get('window', '#fafafa')
            if isinstance(window_color, QColor):
                window_color = window_color.name()
            base_color = colors.get('base', '#ffffff')
            if isinstance(base_color, QColor):
                base_color = base_color.name()
            
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {window_color};
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                }}
            """)
            self.header.setStyleSheet(f"""
                QFrame {{
                    background-color: {header_color};
                    border-radius: 4px;
                }}
            """)
            self.content.setStyleSheet(f"""
                QFrame {{
                    background-color: {base_color};
                    border-radius: 4px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #fafafa;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                }
            """)
            self.header.setStyleSheet("""
                QFrame {
                    background-color: #4285f4;
                    border-radius: 4px;
                }
            """)
            self.content.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border-radius: 4px;
                }
            """)


class SettingsDialog(QDialog):
    settings_applied = pyqtSignal()

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self._original_settings = self._save_current_settings()
        self.setWindowTitle('⚙️ 个性化设置')
        self.setMinimumSize(700, 600)
        self.init_ui()
        self.load_settings()

    def _save_current_settings(self):
        return {
            'theme': self.settings.get_theme(),
            'custom_theme_colors': self.settings.get_custom_theme_colors().copy(),
            'currency_code': self.settings.get_currency_code(),
            'decimal_places': self.settings.get_decimal_places(),
            'date_format': self.settings.get_date_format(),
            'show_currency_symbol': self.settings.get_show_currency_symbol(),
            'tab_order': self.settings.get_tab_order().copy(),
            'highlight_tabs': self.settings.get_highlight_tabs().copy(),
            'highlight_color': self.settings.get_highlight_color(),
        }

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel('⚙️ 个性化设置')
        title_label.setFont(QFont('Microsoft YaHei', 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_theme_tab(), '🎨 主题设置')
        self.tab_widget.addTab(self.create_currency_tab(), '💱 货币设置')
        self.tab_widget.addTab(self.create_format_tab(), '📅 格式设置')
        self.tab_widget.addTab(self.create_layout_tab(), '📐 布局设置')
        layout.addWidget(self.tab_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.reset_btn = QPushButton('恢复默认')
        self.reset_btn.setMinimumWidth(100)
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)

        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.cancel_and_restore)
        button_layout.addWidget(self.cancel_btn)

        self.apply_btn = QPushButton('应用')
        self.apply_btn.setMinimumWidth(100)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #34a853;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d8e47;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)

        self.ok_btn = QPushButton('确定')
        self.ok_btn.setMinimumWidth(100)
        self.ok_btn.setStyleSheet("""
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
        """)
        self.ok_btn.clicked.connect(self.accept_and_apply)
        button_layout.addWidget(self.ok_btn)

        layout.addLayout(button_layout)

    def create_theme_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        theme_group = QGroupBox('主题选择')
        theme_layout = QVBoxLayout(theme_group)

        self.theme_group = QButtonGroup(self)
        self.light_radio = QRadioButton('☀️ 亮色主题')
        self.dark_radio = QRadioButton('🌙 暗色主题')
        self.custom_radio = QRadioButton('🎨 自定义主题')

        self.theme_group.addButton(self.light_radio)
        self.theme_group.addButton(self.dark_radio)
        self.theme_group.addButton(self.custom_radio)

        theme_layout.addWidget(self.light_radio)
        theme_layout.addWidget(self.dark_radio)
        theme_layout.addWidget(self.custom_radio)

        self.light_radio.toggled.connect(self.on_theme_changed)
        self.dark_radio.toggled.connect(self.on_theme_changed)
        self.custom_radio.toggled.connect(self.on_theme_changed)

        layout.addWidget(theme_group)

        self.preview_group = QGroupBox('主题预览')
        preview_layout = QVBoxLayout(self.preview_group)
        self.theme_preview = ThemePreviewWidget()
        preview_layout.addWidget(self.theme_preview)
        layout.addWidget(self.preview_group)

        self.custom_colors_group = QGroupBox('自定义主题颜色')
        custom_colors_layout = QVBoxLayout(self.custom_colors_group)

        color_controls = [
            ('header_bg', '标题栏颜色:', '#4285f4'),
            ('highlight', '高亮颜色:', '#4285f4'),
            ('success', '成功颜色:', '#34a853'),
            ('danger', '危险颜色:', '#ea4335'),
        ]

        self.color_buttons = {}
        self.color_labels = {}

        for key, label_text, default_color in color_controls:
            row_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setMinimumWidth(100)
            row_layout.addWidget(label)

            color_label = QLabel()
            color_label.setFixedSize(100, 30)
            color_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {default_color};
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }}
            """)
            self.color_labels[key] = color_label
            row_layout.addWidget(color_label)

            color_btn = QPushButton('选择颜色...')
            color_btn.setMinimumWidth(100)
            color_btn.clicked.connect(lambda checked, k=key: self.choose_color(k))
            self.color_buttons[key] = color_btn
            row_layout.addWidget(color_btn)

            row_layout.addStretch()
            custom_colors_layout.addLayout(row_layout)

        layout.addWidget(self.custom_colors_group)
        layout.addStretch()

        return widget

    def create_currency_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        currency_group = QGroupBox('货币单位')
        currency_layout = QVBoxLayout(currency_group)

        currency_select_layout = QHBoxLayout()
        currency_label = QLabel('显示货币:')
        currency_label.setMinimumWidth(80)
        currency_select_layout.addWidget(currency_label)

        self.currency_combo = QComboBox()
        for code, currency in CURRENCIES.items():
            self.currency_combo.addItem(f"{currency.symbol} {currency.name} ({code})", code)
        self.currency_combo.setMinimumWidth(200)
        currency_select_layout.addWidget(self.currency_combo)
        currency_select_layout.addStretch()

        currency_layout.addLayout(currency_select_layout)

        self.show_symbol_check = QCheckBox('显示货币符号')
        currency_layout.addWidget(self.show_symbol_check)

        layout.addWidget(currency_group)

        decimal_group = QGroupBox('小数位数')
        decimal_layout = QVBoxLayout(decimal_group)

        decimal_select_layout = QHBoxLayout()
        decimal_label = QLabel('金额显示小数位数:')
        decimal_label.setMinimumWidth(120)
        decimal_select_layout.addWidget(decimal_label)

        self.decimal_spin = QSpinBox()
        self.decimal_spin.setRange(0, 6)
        self.decimal_spin.setMinimumWidth(80)
        self.decimal_spin.setSpecialValueText('不显示小数')
        decimal_select_layout.addWidget(self.decimal_spin)

        decimal_example_label = QLabel('示例:')
        decimal_select_layout.addWidget(decimal_example_label)

        self.decimal_example = QLabel('¥ 1,234.56')
        self.decimal_example.setStyleSheet("font-weight: bold; color: #4285f4;")
        decimal_select_layout.addWidget(self.decimal_example)

        decimal_select_layout.addStretch()
        decimal_layout.addLayout(decimal_select_layout)

        self.decimal_spin.valueChanged.connect(self.update_decimal_example)

        layout.addWidget(decimal_group)

        exchange_group = QGroupBox('汇率设置 (相对于人民币)')
        exchange_layout = QVBoxLayout(exchange_group)

        exchange_info = QLabel('以下汇率为示例汇率，实际汇率请根据当前市场汇率手动设置。\n汇率用于不同货币单位之间的金额转换显示。')
        exchange_info.setStyleSheet("color: #5f6368;")
        exchange_info.setWordWrap(True)
        exchange_layout.addWidget(exchange_info)

        self.exchange_controls = {}
        for code, currency in CURRENCIES.items():
            if code == 'CNY':
                continue
            row_layout = QHBoxLayout()
            code_label = QLabel(f"{currency.symbol} {currency.name} ({code}):")
            code_label.setMinimumWidth(150)
            row_layout.addWidget(code_label)

            rate_label = QLabel('1 CNY = ')
            row_layout.addWidget(rate_label)

            rate_spin = QDoubleSpinBox()
            rate_spin.setRange(0.0001, 1000.0)
            rate_spin.setDecimals(4)
            rate_spin.setSingleStep(0.01)
            rate_spin.setValue(currency.rate)
            rate_spin.setMinimumWidth(100)
            self.exchange_controls[code] = rate_spin
            row_layout.addWidget(rate_spin)

            code_label2 = QLabel(f' {code}')
            row_layout.addWidget(code_label2)

            row_layout.addStretch()
            exchange_layout.addLayout(row_layout)

        layout.addWidget(exchange_group)
        layout.addStretch()

        return widget

    def create_format_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        date_group = QGroupBox('日期格式')
        date_layout = QVBoxLayout(date_group)

        date_select_layout = QHBoxLayout()
        date_label = QLabel('选择日期显示格式:')
        date_label.setMinimumWidth(120)
        date_select_layout.addWidget(date_label)

        self.date_combo = QComboBox()
        date_formats = [
            ('yyyy-MM-dd', '2024-01-15 (ISO 格式)'),
            ('yyyy/MM/dd', '2024/01/15'),
            ('MM/dd/yyyy', '01/15/2024 (美式)'),
            ('dd/MM/yyyy', '15/01/2024 (欧式)'),
            ('yyyy年MM月dd日', '2024年01月15日 (中文)'),
        ]
        for format_code, display_text in date_formats:
            self.date_combo.addItem(display_text, format_code)
        self.date_combo.setMinimumWidth(250)
        date_select_layout.addWidget(self.date_combo)
        date_select_layout.addStretch()

        date_layout.addLayout(date_select_layout)

        preview_layout = QHBoxLayout()
        preview_label = QLabel('预览:')
        preview_layout.addWidget(preview_label)

        self.date_preview = QLabel('2024-01-15')
        self.date_preview.setStyleSheet("font-weight: bold; color: #4285f4; font-size: 14px;")
        preview_layout.addWidget(self.date_preview)

        preview_layout.addStretch()
        date_layout.addLayout(preview_layout)

        self.date_combo.currentIndexChanged.connect(self.update_date_preview)

        layout.addWidget(date_group)

        example_group = QGroupBox('格式应用示例')
        example_layout = QVBoxLayout(example_group)

        examples = [
            ('交易日期显示', '将影响所有日期字段的显示格式'),
            ('报表日期范围', '筛选和统计中的日期显示'),
            ('导出数据格式', 'CSV/Excel 导出时的日期格式'),
        ]

        for title, desc in examples:
            row_layout = QHBoxLayout()
            title_label = QLabel(f"• {title}")
            title_label.setStyleSheet("font-weight: bold;")
            row_layout.addWidget(title_label)
            desc_label = QLabel(f"- {desc}")
            desc_label.setStyleSheet("color: #5f6368;")
            row_layout.addWidget(desc_label)
            row_layout.addStretch()
            example_layout.addLayout(row_layout)

        layout.addWidget(example_group)
        layout.addStretch()

        return widget

    def create_layout_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)

        tab_order_group = QGroupBox('标签页顺序')
        tab_order_layout = QVBoxLayout(tab_order_group)

        order_info = QLabel('调整标签页的显示顺序。点击标签后使用上下按钮调整位置。')
        order_info.setStyleSheet("color: #5f6368;")
        order_info.setWordWrap(True)
        tab_order_layout.addWidget(order_info)

        order_control_layout = QHBoxLayout()

        self.tab_list = QListWidget()
        self.tab_list.setMinimumHeight(200)
        self.tab_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        order_control_layout.addWidget(self.tab_list, 1)

        btn_layout = QVBoxLayout()

        self.move_up_btn = QPushButton('▲ 上移')
        self.move_up_btn.clicked.connect(self.move_tab_up)
        btn_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton('▼ 下移')
        self.move_down_btn.clicked.connect(self.move_tab_down)
        btn_layout.addWidget(self.move_down_btn)

        btn_layout.addStretch()

        order_control_layout.addLayout(btn_layout)
        tab_order_layout.addLayout(order_control_layout)

        layout.addWidget(tab_order_group)

        highlight_group = QGroupBox('标签页高亮')
        highlight_layout = QVBoxLayout(highlight_group)

        highlight_info = QLabel('选择需要特殊高亮显示的标签页（常用模块前置提示）。')
        highlight_info.setStyleSheet("color: #5f6368;")
        highlight_info.setWordWrap(True)
        highlight_layout.addWidget(highlight_info)

        self.highlight_checkboxes = {}
        for tab_key, tab_label in SettingsManager.TAB_LABELS.items():
            check = QCheckBox(tab_label)
            self.highlight_checkboxes[tab_key] = check
            highlight_layout.addWidget(check)

        color_row = QHBoxLayout()
        color_label = QLabel('高亮颜色:')
        color_row.addWidget(color_label)

        self.highlight_color_label = QLabel()
        self.highlight_color_label.setFixedSize(100, 30)
        self.highlight_color_label.setStyleSheet("""
            QLabel {
                background-color: #ff9800;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)
        color_row.addWidget(self.highlight_color_label)

        self.highlight_color_btn = QPushButton('选择颜色...')
        self.highlight_color_btn.clicked.connect(self.choose_highlight_color)
        color_row.addWidget(self.highlight_color_btn)

        color_row.addStretch()
        highlight_layout.addLayout(color_row)

        layout.addWidget(highlight_group)
        layout.addStretch()

        return widget

    def load_settings(self):
        theme = self.settings.get_theme()
        if theme == 'light':
            self.light_radio.setChecked(True)
        elif theme == 'dark':
            self.dark_radio.setChecked(True)
        else:
            self.custom_radio.setChecked(True)

        custom_colors = self.settings.get_custom_theme_colors()
        for key, color_value in custom_colors.items():
            if key in self.color_labels:
                if isinstance(color_value, str):
                    color_name = color_value
                else:
                    color_name = QColor(*color_value).name() if color_value else '#4285f4'
                self.color_labels[key].setStyleSheet(f"""
                    QLabel {{
                        background-color: {color_name};
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                    }}
                """)

        currency_code = self.settings.get_currency_code()
        for i in range(self.currency_combo.count()):
            if self.currency_combo.itemData(i) == currency_code:
                self.currency_combo.setCurrentIndex(i)
                break

        self.show_symbol_check.setChecked(self.settings.get_show_currency_symbol())
        self.decimal_spin.setValue(self.settings.get_decimal_places())
        self.update_decimal_example()

        date_format = self.settings.get_date_format()
        for i in range(self.date_combo.count()):
            if self.date_combo.itemData(i) == date_format:
                self.date_combo.setCurrentIndex(i)
                break
        self.update_date_preview()

        tab_order = self.settings.get_tab_order()
        self.tab_list.clear()
        for tab_key in tab_order:
            item = QListWidgetItem(self.settings.get_tab_label(tab_key))
            item.setData(Qt.ItemDataRole.UserRole, tab_key)
            self.tab_list.addItem(item)

        highlight_tabs = self.settings.get_highlight_tabs()
        for tab_key, check in self.highlight_checkboxes.items():
            check.setChecked(tab_key in highlight_tabs)

        highlight_color = self.settings.get_highlight_color()
        self.highlight_color_label.setStyleSheet(f"""
            QLabel {{
                background-color: {highlight_color};
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }}
        """)

        self.on_theme_changed()

    def on_theme_changed(self):
        is_custom = self.custom_radio.isChecked()
        self.custom_colors_group.setEnabled(is_custom)
        
        if self.dark_radio.isChecked():
            self.theme_preview.set_theme('dark')
        elif is_custom:
            colors = self.settings.get_theme_colors()
            self.theme_preview.set_theme('custom', colors)
        else:
            self.theme_preview.set_theme('light')

    def choose_color(self, color_key):
        current_color = QColor('#4285f4')
        custom_colors = self.settings.get_custom_theme_colors()
        if color_key in custom_colors:
            color_value = custom_colors[color_key]
            if isinstance(color_value, str):
                current_color = QColor(color_value)
            elif color_value:
                current_color = QColor(*color_value)

        color = QColorDialog.getColor(current_color, self, '选择颜色')
        
        if color.isValid():
            self.color_labels[color_key].setStyleSheet(f"""
                QLabel {{
                    background-color: {color.name()};
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }}
            """)
            
            custom_colors = self.settings.get_custom_theme_colors().copy()
            custom_colors[color_key] = color.name()
            self.settings.set_custom_theme_colors(custom_colors)
            
            if self.custom_radio.isChecked():
                self.theme_preview.set_theme('custom', self.settings.get_theme_colors())

    def choose_highlight_color(self):
        current_color = QColor(self.settings.get_highlight_color())
        color = QColorDialog.getColor(current_color, self, '选择高亮颜色')
        
        if color.isValid():
            self.highlight_color_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color.name()};
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                }}
            """)
            self.settings.set_highlight_color(color.name())

    def update_decimal_example(self):
        decimal_places = self.decimal_spin.value()
        currency = self.settings.get_currency()
        amount = 1234.5678
        
        if decimal_places == 0:
            formatted = f"{currency.symbol} {int(amount):,}"
        else:
            formatted = f"{currency.symbol} {amount:,.{decimal_places}f}"
        
        self.decimal_example.setText(formatted)

    def update_date_preview(self):
        format_code = self.date_combo.currentData()
        example_date = '2024-01-15'
        
        year, month, day = example_date.split('-')
        
        format_map = {
            'yyyy-MM-dd': f'{year}-{month}-{day}',
            'yyyy/MM/dd': f'{year}/{month}/{day}',
            'MM/dd/yyyy': f'{month}/{day}/{year}',
            'dd/MM/yyyy': f'{day}/{month}/{year}',
            'yyyy年MM月dd日': f'{year}年{month}月{day}日',
        }
        
        self.date_preview.setText(format_map.get(format_code, example_date))

    def move_tab_up(self):
        current_row = self.tab_list.currentRow()
        if current_row > 0:
            item = self.tab_list.takeItem(current_row)
            self.tab_list.insertItem(current_row - 1, item)
            self.tab_list.setCurrentRow(current_row - 1)

    def move_tab_down(self):
        current_row = self.tab_list.currentRow()
        if current_row < self.tab_list.count() - 1:
            item = self.tab_list.takeItem(current_row)
            self.tab_list.insertItem(current_row + 1, item)
            self.tab_list.setCurrentRow(current_row + 1)

    def apply_settings(self):
        if self.light_radio.isChecked():
            self.settings.set_theme('light')
        elif self.dark_radio.isChecked():
            self.settings.set_theme('dark')
        else:
            self.settings.set_theme('custom')

        currency_code = self.currency_combo.currentData()
        self.settings.set_currency_code(currency_code)
        self.settings.set_show_currency_symbol(self.show_symbol_check.isChecked())
        self.settings.set_decimal_places(self.decimal_spin.value())
        self.settings.set_date_format(self.date_combo.currentData())

        for code, spin in self.exchange_controls.items():
            if code in CURRENCIES:
                CURRENCIES[code].rate = spin.value()

        new_order = []
        for i in range(self.tab_list.count()):
            item = self.tab_list.item(i)
            new_order.append(item.data(Qt.ItemDataRole.UserRole))
        self.settings.set_tab_order(new_order)

        highlight_tabs = []
        for tab_key, check in self.highlight_checkboxes.items():
            if check.isChecked():
                highlight_tabs.append(tab_key)
        self.settings.set_highlight_tabs(highlight_tabs)

        self._original_settings = self._save_current_settings()
        self.settings_applied.emit()

        QMessageBox.information(self, '设置已应用', '设置已成功应用，部分更改可能需要重启应用才能完全生效。')

    def reset_to_defaults(self):
        reply = QMessageBox.question(
            self, '确认恢复默认',
            '确定要将所有设置恢复为默认值吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for key, default_value in SettingsManager.DEFAULT_SETTINGS.items():
                self.settings._save_setting(key, default_value)
            
            for code, currency in CURRENCIES.items():
                if code == 'CNY':
                    currency.rate = 1.0
                elif code == 'USD':
                    currency.rate = 7.25
                elif code == 'EUR':
                    currency.rate = 7.8
                elif code == 'GBP':
                    currency.rate = 9.1
                elif code == 'JPY':
                    currency.rate = 0.048
                elif code == 'HKD':
                    currency.rate = 0.93

            self.load_settings()
            self.settings_applied.emit()

    def cancel_and_restore(self):
        for key, value in self._original_settings.items():
            if key == 'theme':
                self.settings._save_setting('theme', value)
            elif key == 'custom_theme_colors':
                self.settings._save_setting('custom_theme_colors', value.copy())
            elif key == 'currency_code':
                self.settings._save_setting('currency_code', value)
            elif key == 'decimal_places':
                self.settings._save_setting('decimal_places', value)
            elif key == 'date_format':
                self.settings._save_setting('date_format', value)
            elif key == 'show_currency_symbol':
                self.settings._save_setting('show_currency_symbol', value)
            elif key == 'tab_order':
                self.settings._save_setting('tab_order', value.copy())
            elif key == 'highlight_tabs':
                self.settings._save_setting('highlight_tabs', value.copy())
            elif key == 'highlight_color':
                self.settings._save_setting('highlight_color', value)
        
        self.reject()

    def accept_and_apply(self):
        self.apply_settings()
        self.accept()
