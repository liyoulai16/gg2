from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QRadioButton,
    QButtonGroup, QInputDialog, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt


class CategoryWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        add_group = QGroupBox('添加分类')
        add_layout = QHBoxLayout(add_group)

        type_group = QGroupBox('类型')
        type_layout = QVBoxLayout(type_group)
        self.type_group = QButtonGroup(self)
        self.income_radio = QRadioButton('💰 收入')
        self.expense_radio = QRadioButton('💸 支出')
        self.expense_radio.setChecked(True)
        self.type_group.addButton(self.income_radio)
        self.type_group.addButton(self.expense_radio)
        type_layout.addWidget(self.income_radio)
        type_layout.addWidget(self.expense_radio)
        add_layout.addWidget(type_group)

        name_label = QLabel('分类名称:')
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('例如：餐饮、交通、工资...')
        add_layout.addWidget(name_label)
        add_layout.addWidget(self.name_edit)

        add_btn = QPushButton('✓ 添加分类')
        add_btn.setMinimumWidth(100)
        add_btn.clicked.connect(self.add_category)
        add_layout.addWidget(add_btn)

        add_layout.addStretch()
        layout.addWidget(add_group)

        stats_group = QGroupBox('分类统计')
        stats_layout = QHBoxLayout(stats_group)

        self.income_count_label = QLabel('收入分类: 0 个')
        self.income_count_label.setStyleSheet("font-size: 14px; color: #34a853;")
        stats_layout.addWidget(self.income_count_label)

        self.expense_count_label = QLabel('支出分类: 0 个')
        self.expense_count_label.setStyleSheet("font-size: 14px; color: #ea4335;")
        stats_layout.addWidget(self.expense_count_label)

        stats_layout.addStretch()

        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self.refresh_data)
        stats_layout.addWidget(refresh_btn)

        layout.addWidget(stats_group)

        tables_layout = QHBoxLayout()

        income_group = QGroupBox('💰 收入分类')
        income_layout = QVBoxLayout(income_group)

        self.income_table = QTableWidget()
        self.income_table.setColumnCount(4)
        self.income_table.setHorizontalHeaderLabels(['ID', '分类名称', '创建时间', '操作'])
        self.income_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.income_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.income_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.income_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.income_table.setAlternatingRowColors(True)
        income_layout.addWidget(self.income_table)

        tables_layout.addWidget(income_group)

        expense_group = QGroupBox('💸 支出分类')
        expense_layout = QVBoxLayout(expense_group)

        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(4)
        self.expense_table.setHorizontalHeaderLabels(['ID', '分类名称', '创建时间', '操作'])
        self.expense_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.expense_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.expense_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.expense_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.expense_table.setAlternatingRowColors(True)
        expense_layout.addWidget(self.expense_table)

        tables_layout.addWidget(expense_group)

        layout.addLayout(tables_layout)

    def refresh_data(self):
        income_categories = self.db.get_all_categories('income')
        expense_categories = self.db.get_all_categories('expense')

        self.update_category_table(self.income_table, income_categories, 'income')
        self.update_category_table(self.expense_table, expense_categories, 'expense')

        self.income_count_label.setText(f'收入分类: {len(income_categories)} 个')
        self.expense_count_label.setText(f'支出分类: {len(expense_categories)} 个')

    def update_category_table(self, table, categories, type_):
        table.setRowCount(len(categories))

        for row, category in enumerate(categories):
            table.setItem(row, 0, QTableWidgetItem(str(category['id'])))
            table.setItem(row, 1, QTableWidgetItem(category['name']))
            table.setItem(row, 2, QTableWidgetItem(category['created_at']))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 0, 5, 0)

            edit_btn = QPushButton('编辑')
            edit_btn.setMinimumWidth(55)
            edit_btn.setMinimumHeight(28)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4285f4;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3367d6;
                }
            """)
            edit_btn.clicked.connect(lambda checked, c=category, t=type_: self.edit_category(c, t))
            btn_layout.addWidget(edit_btn)

            delete_btn = QPushButton('删除')
            delete_btn.setMinimumWidth(55)
            delete_btn.setMinimumHeight(28)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ea4335;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d33427;
                }
            """)
            delete_btn.clicked.connect(lambda checked, c_id=category['id']: self.delete_category(c_id))
            btn_layout.addWidget(delete_btn)

            table.setCellWidget(row, 3, btn_widget)

    def add_category(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '警告', '请输入分类名称！')
            return

        type_ = 'income' if self.income_radio.isChecked() else 'expense'

        if self.db.add_category(name, type_):
            type_text = '收入' if type_ == 'income' else '支出'
            QMessageBox.information(self, '成功', f'{type_text}分类"{name}"添加成功！')
            self.name_edit.clear()
            self.refresh_data()
        else:
            QMessageBox.warning(self, '警告', f'该类型下已存在分类"{name}"！')

    def edit_category(self, category, type_):
        new_name, ok = QInputDialog.getText(
            self, '编辑分类',
            f'当前分类: {category["name"]}\n类型: {"收入" if type_ == "income" else "支出"}\n\n请输入新的分类名称:',
            text=category['name']
        )

        if ok and new_name.strip():
            if self.db.update_category(category['id'], name=new_name.strip()):
                QMessageBox.information(self, '成功', '分类信息已更新！')
                self.refresh_data()
            else:
                QMessageBox.warning(self, '警告', '分类名称已存在或更新失败！')

    def delete_category(self, category_id):
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这个分类吗？\n注意：只有没有交易记录的分类才能删除。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_category(category_id):
                QMessageBox.information(self, '成功', '分类已删除！')
                self.refresh_data()
            else:
                QMessageBox.warning(self, '警告', '删除失败！该分类可能有交易记录。')
