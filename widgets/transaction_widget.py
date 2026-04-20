from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QRadioButton,
    QButtonGroup, QDateEdit, QMessageBox, QDoubleSpinBox,
    QSplitter, QFrame, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime


class TransactionWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        add_group = QGroupBox('添加收支记录')
        add_layout = QVBoxLayout(add_group)

        form_layout = QHBoxLayout()

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
        form_layout.addWidget(type_group)

        self.income_radio.toggled.connect(self.on_type_changed)

        account_label = QLabel('账户:')
        self.account_combo = QComboBox()
        form_layout.addWidget(account_label)
        form_layout.addWidget(self.account_combo)

        category_label = QLabel('分类:')
        self.category_combo = QComboBox()
        form_layout.addWidget(category_label)
        form_layout.addWidget(self.category_combo)

        amount_label = QLabel('金额:')
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix('¥ ')
        self.amount_spin.setValue(0)
        form_layout.addWidget(amount_label)
        form_layout.addWidget(self.amount_spin)

        date_label = QLabel('日期:')
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addWidget(date_label)
        form_layout.addWidget(self.date_edit)

        add_layout.addLayout(form_layout)

        desc_layout = QHBoxLayout()
        desc_label = QLabel('描述:')
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText('可选，输入备注信息...')
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_edit)

        add_btn = QPushButton('✓ 添加记录')
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(self.add_transaction)
        desc_layout.addWidget(add_btn)

        add_layout.addLayout(desc_layout)
        layout.addWidget(add_group)

        filter_group = QGroupBox('筛选记录')
        filter_layout = QHBoxLayout(filter_group)

        filter_account_label = QLabel('账户:')
        self.filter_account_combo = QComboBox()
        filter_layout.addWidget(filter_account_label)
        filter_layout.addWidget(self.filter_account_combo)

        filter_type_label = QLabel('类型:')
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(['全部', '收入', '支出'])
        filter_layout.addWidget(filter_type_label)
        filter_layout.addWidget(self.filter_type_combo)

        start_date_label = QLabel('开始日期:')
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        filter_layout.addWidget(start_date_label)
        filter_layout.addWidget(self.start_date_edit)

        end_date_label = QLabel('结束日期:')
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        filter_layout.addWidget(end_date_label)
        filter_layout.addWidget(self.end_date_edit)

        filter_btn = QPushButton('🔍 筛选')
        filter_btn.clicked.connect(self.filter_transactions)
        filter_layout.addWidget(filter_btn)

        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        stats_group = QGroupBox('统计概览')
        stats_layout = QHBoxLayout(stats_group)

        self.total_income_label = QLabel('本期收入: ¥ 0.00')
        self.total_income_label.setStyleSheet("color: #34a853; font-size: 14px; font-weight: bold; padding: 10px;")
        stats_layout.addWidget(self.total_income_label)

        self.total_expense_label = QLabel('本期支出: ¥ 0.00')
        self.total_expense_label.setStyleSheet("color: #ea4335; font-size: 14px; font-weight: bold; padding: 10px;")
        stats_layout.addWidget(self.total_expense_label)

        self.net_income_label = QLabel('本期结余: ¥ 0.00')
        self.net_income_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        stats_layout.addWidget(self.net_income_label)

        stats_layout.addStretch()
        layout.addWidget(stats_group)

        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(7)
        self.trans_table.setHorizontalHeaderLabels([
            '日期', '账户', '类型', '分类', '金额', '描述', '操作'
        ])
        self.trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trans_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.trans_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.trans_table.setAlternatingRowColors(True)
        layout.addWidget(self.trans_table)

    def refresh_data(self):
        self.load_accounts()
        self.load_categories()
        self.filter_transactions()
        self.load_filter_accounts()

    def load_accounts(self):
        accounts = self.db.get_all_accounts()
        self.account_combo.clear()
        for account in accounts:
            self.account_combo.addItem(f"{account['name']} (¥ {account['balance']:,.2f})", account['id'])

    def load_filter_accounts(self):
        accounts = self.db.get_all_accounts()
        self.filter_account_combo.clear()
        self.filter_account_combo.addItem('全部账户', None)
        for account in accounts:
            self.filter_account_combo.addItem(account['name'], account['id'])

    def load_categories(self):
        type_ = 'income' if self.income_radio.isChecked() else 'expense'
        categories = self.db.get_all_categories(type_)
        self.category_combo.clear()
        for category in categories:
            self.category_combo.addItem(category['name'], category['id'])

    def on_type_changed(self):
        self.load_categories()

    def add_transaction(self):
        account_id = self.account_combo.currentData()
        if account_id is None:
            QMessageBox.warning(self, '警告', '请先添加账户！')
            return

        category_id = self.category_combo.currentData()
        if category_id is None:
            QMessageBox.warning(self, '警告', '请选择分类！')
            return

        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, '警告', '请输入有效的金额！')
            return

        type_ = 'income' if self.income_radio.isChecked() else 'expense'
        description = self.desc_edit.text().strip()
        date = self.date_edit.date().toString('yyyy-MM-dd')

        if self.db.add_transaction(account_id, category_id, type_, amount, description, date):
            QMessageBox.information(self, '成功', '记录添加成功！')
            self.amount_spin.setValue(0)
            self.desc_edit.clear()
            self.refresh_data()
            self.parent().parent().update_status_bar()
        else:
            QMessageBox.critical(self, '错误', '添加记录失败！')

    def filter_transactions(self):
        account_id = self.filter_account_combo.currentData()
        type_text = self.filter_type_combo.currentText()
        start_date = self.start_date_edit.date().toString('yyyy-MM-dd')
        end_date = self.end_date_edit.date().toString('yyyy-MM-dd')

        type_ = None
        if type_text == '收入':
            type_ = 'income'
        elif type_text == '支出':
            type_ = 'expense'

        transactions = self.db.get_transactions(account_id, start_date, end_date, type_)
        self.update_transaction_table(transactions)
        self.update_stats(transactions)

    def update_transaction_table(self, transactions):
        self.trans_table.setRowCount(len(transactions))

        for row, trans in enumerate(transactions):
            self.trans_table.setItem(row, 0, QTableWidgetItem(trans['date']))
            self.trans_table.setItem(row, 1, QTableWidgetItem(trans['account_name']))

            type_item = QTableWidgetItem('收入' if trans['type'] == 'income' else '支出')
            if trans['type'] == 'income':
                type_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                type_item.setForeground(Qt.GlobalColor.darkRed)
            self.trans_table.setItem(row, 2, type_item)

            self.trans_table.setItem(row, 3, QTableWidgetItem(trans['category_name']))

            amount = trans['amount']
            amount_str = f'+¥ {amount:,.2f}' if trans['type'] == 'income' else f'-¥ {amount:,.2f}'
            amount_item = QTableWidgetItem(amount_str)
            if trans['type'] == 'income':
                amount_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                amount_item.setForeground(Qt.GlobalColor.darkRed)
            self.trans_table.setItem(row, 4, amount_item)

            self.trans_table.setItem(row, 5, QTableWidgetItem(trans['description'] or '-'))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(5, 0, 5, 0)

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
            delete_btn.clicked.connect(lambda checked, t_id=trans['id']: self.delete_transaction(t_id))
            btn_layout.addWidget(delete_btn)

            self.trans_table.setCellWidget(row, 6, btn_widget)

    def update_stats(self, transactions):
        total_income = sum(t['amount'] for t in transactions if t['type'] == 'income')
        total_expense = sum(t['amount'] for t in transactions if t['type'] == 'expense')
        net_income = total_income - total_expense

        self.total_income_label.setText(f'本期收入: ¥ {total_income:,.2f}')
        self.total_expense_label.setText(f'本期支出: ¥ {total_expense:,.2f}')

        if net_income >= 0:
            self.net_income_label.setText(f'本期结余: +¥ {net_income:,.2f}')
            self.net_income_label.setStyleSheet("color: #34a853; font-size: 14px; font-weight: bold; padding: 10px;")
        else:
            self.net_income_label.setText(f'本期结余: -¥ {abs(net_income):,.2f}')
            self.net_income_label.setStyleSheet("color: #ea4335; font-size: 14px; font-weight: bold; padding: 10px;")

    def delete_transaction(self, transaction_id):
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这条记录吗？此操作不可恢复。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_transaction(transaction_id):
                QMessageBox.information(self, '成功', '记录已删除！')
                self.refresh_data()
                self.parent().parent().update_status_bar()
            else:
                QMessageBox.critical(self, '错误', '删除记录失败！')
