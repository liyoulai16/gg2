from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QMessageBox, QComboBox, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget
)
from PyQt6.QtCore import Qt


class QuickEntrySettingsDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle('⚙ 快速记账预设设置')
        self.setMinimumSize(600, 500)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        add_group = QGroupBox('添加新预设')
        add_layout = QVBoxLayout(add_group)

        form_layout = QHBoxLayout()

        name_label = QLabel('预设名称:')
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('例如：午餐、打车...')
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_edit)

        type_label = QLabel('类型:')
        self.type_group = QButtonGroup(self)
        self.income_radio = QRadioButton('收入')
        self.expense_radio = QRadioButton('支出')
        self.expense_radio.setChecked(True)
        self.type_group.addButton(self.income_radio)
        self.type_group.addButton(self.expense_radio)
        form_layout.addWidget(type_label)
        form_layout.addWidget(self.income_radio)
        form_layout.addWidget(self.expense_radio)

        add_layout.addLayout(form_layout)

        second_row = QHBoxLayout()

        account_label = QLabel('账户:')
        self.account_combo = QComboBox()
        second_row.addWidget(account_label)
        second_row.addWidget(self.account_combo)

        category_label = QLabel('分类:')
        self.category_combo = QComboBox()
        second_row.addWidget(category_label)
        second_row.addWidget(self.category_combo)

        add_layout.addLayout(second_row)

        third_row = QHBoxLayout()

        desc_label = QLabel('描述(可选):')
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText('默认描述...')
        third_row.addWidget(desc_label)
        third_row.addWidget(self.desc_edit)

        self.default_check = QRadioButton('设为默认')
        third_row.addWidget(self.default_check)

        add_btn = QPushButton('➕ 添加预设')
        add_btn.setMinimumWidth(100)
        add_btn.clicked.connect(self.add_preset)
        third_row.addWidget(add_btn)

        add_layout.addLayout(third_row)

        layout.addWidget(add_group)

        list_group = QGroupBox('现有预设')
        list_layout = QVBoxLayout(list_group)

        self.preset_table = QTableWidget()
        self.preset_table.setColumnCount(7)
        self.preset_table.setHorizontalHeaderLabels([
            '预设名称', '类型', '账户', '分类', '描述', '默认', '操作'
        ])
        self.preset_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preset_table.verticalHeader().setDefaultSectionSize(40)
        self.preset_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.preset_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.preset_table.setAlternatingRowColors(True)

        list_layout.addWidget(self.preset_table)

        layout.addWidget(list_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(refresh_btn)

        close_btn = QPushButton('✓ 关闭')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        self.income_radio.toggled.connect(self.on_type_changed)

    def load_data(self):
        self.load_accounts()
        self.load_categories()
        self.load_presets()

    def load_accounts(self):
        accounts = self.db.get_all_accounts()
        self.account_combo.clear()
        for account in accounts:
            self.account_combo.addItem(account['name'], account['id'])

    def load_categories(self):
        type_ = 'income' if self.income_radio.isChecked() else 'expense'
        categories = self.db.get_all_categories(type_)
        self.category_combo.clear()
        for category in categories:
            self.category_combo.addItem(category['name'], category['id'])

    def on_type_changed(self):
        self.load_categories()

    def load_presets(self):
        presets = self.db.get_all_quick_entry_presets()
        self.preset_table.setRowCount(len(presets))

        for row, preset in enumerate(presets):
            self.preset_table.setItem(row, 0, QTableWidgetItem(preset['name']))
            
            type_item = QTableWidgetItem('收入' if preset['type'] == 'income' else '支出')
            if preset['type'] == 'income':
                type_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                type_item.setForeground(Qt.GlobalColor.darkRed)
            self.preset_table.setItem(row, 1, type_item)

            self.preset_table.setItem(row, 2, QTableWidgetItem(preset['account_name']))
            self.preset_table.setItem(row, 3, QTableWidgetItem(preset['category_name']))
            self.preset_table.setItem(row, 4, QTableWidgetItem(preset['description'] or '-'))
            
            default_item = QTableWidgetItem('✓' if preset['is_default'] else '')
            if preset['is_default']:
                default_item.setForeground(Qt.GlobalColor.darkGreen)
            self.preset_table.setItem(row, 5, default_item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(5)

            if not preset['is_default']:
                set_default_btn = QPushButton('设为默认')
                set_default_btn.setFixedSize(70, 28)
                set_default_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #34a853;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #2d8e47;
                    }
                """)
                set_default_btn.clicked.connect(lambda checked, p_id=preset['id']: self.set_default_preset(p_id))
                btn_layout.addWidget(set_default_btn)

            delete_btn = QPushButton('删除')
            delete_btn.setFixedSize(50, 28)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ea4335;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #d33427;
                }
            """)
            delete_btn.clicked.connect(lambda checked, p_id=preset['id']: self.delete_preset(p_id))
            btn_layout.addWidget(delete_btn)

            self.preset_table.setCellWidget(row, 6, btn_widget)

    def add_preset(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '警告', '请输入预设名称！')
            return

        account_id = self.account_combo.currentData()
        if account_id is None:
            QMessageBox.warning(self, '警告', '请选择账户！')
            return

        category_id = self.category_combo.currentData()
        if category_id is None:
            QMessageBox.warning(self, '警告', '请选择分类！')
            return

        type_ = 'income' if self.income_radio.isChecked() else 'expense'
        description = self.desc_edit.text().strip()
        is_default = self.default_check.isChecked()

        if self.db.add_quick_entry_preset(name, type_, account_id, category_id, description, is_default):
            QMessageBox.information(self, '成功', '预设添加成功！')
            self.name_edit.clear()
            self.desc_edit.clear()
            self.default_check.setChecked(False)
            self.load_presets()
        else:
            QMessageBox.critical(self, '错误', '添加预设失败！可能名称已存在。')

    def set_default_preset(self, preset_id):
        if self.db.update_quick_entry_preset(preset_id, is_default=True):
            QMessageBox.information(self, '成功', '已设为默认预设！')
            self.load_presets()
        else:
            QMessageBox.critical(self, '错误', '设置失败！')

    def delete_preset(self, preset_id):
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这个预设吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_quick_entry_preset(preset_id):
                QMessageBox.information(self, '成功', '预设已删除！')
                self.load_presets()
            else:
                QMessageBox.critical(self, '错误', '删除失败！')
