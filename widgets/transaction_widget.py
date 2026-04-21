from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QRadioButton,
    QButtonGroup, QDateEdit, QMessageBox, QDoubleSpinBox,
    QSplitter, QFrame, QHeaderView, QAbstractItemView,
    QApplication, QCheckBox, QSpinBox, QDialog
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from .transaction_management_dialogs import TransactionSplitDialog, TransactionMergeDialog


class TransactionWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.refresh_data()
    
    def find_main_window(self):
        for widget in QApplication.instance().topLevelWidgets():
            if widget.__class__.__name__ == 'MainWindow':
                return widget
        return None

    def eventFilter(self, obj, event):
        if event.type() == event.Type.Wheel:
            if isinstance(obj, (QDoubleSpinBox, QSpinBox, QDateEdit)):
                return True
        return super().eventFilter(obj, event)

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
        form_layout.addSpacing(40)

        category_label = QLabel('分类:')
        self.category_combo = QComboBox()
        form_layout.addWidget(category_label)
        form_layout.addWidget(self.category_combo)
        form_layout.addSpacing(40)

        amount_label = QLabel('金额:')
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix('¥ ')
        self.amount_spin.setValue(0)
        self.amount_spin.installEventFilter(self)
        form_layout.addWidget(amount_label)
        form_layout.addWidget(self.amount_spin)
        form_layout.addSpacing(40)

        date_label = QLabel('日期:')
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.installEventFilter(self)
        form_layout.addWidget(date_label)
        form_layout.addWidget(self.date_edit)

        form_layout.addStretch()
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
        filter_layout.addSpacing(30)

        filter_type_label = QLabel('类型:')
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItems(['全部', '收入', '支出'])
        filter_layout.addWidget(filter_type_label)
        filter_layout.addWidget(self.filter_type_combo)
        filter_layout.addSpacing(30)

        start_date_label = QLabel('开始日期:')
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.installEventFilter(self)
        filter_layout.addWidget(start_date_label)
        filter_layout.addWidget(self.start_date_edit)
        filter_layout.addSpacing(30)

        end_date_label = QLabel('结束日期:')
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.installEventFilter(self)
        filter_layout.addWidget(end_date_label)
        filter_layout.addWidget(self.end_date_edit)
        filter_layout.addSpacing(30)

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

        toolbar_layout = QHBoxLayout()
        
        self.select_all_check = QCheckBox('全选')
        self.select_all_check.stateChanged.connect(self.on_select_all_changed)
        toolbar_layout.addWidget(self.select_all_check)

        toolbar_layout.addSpacing(20)

        merge_btn = QPushButton('🔗 合并选中')
        merge_btn.setMinimumWidth(100)
        merge_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
        """)
        merge_btn.clicked.connect(self.merge_selected_transactions)
        toolbar_layout.addWidget(merge_btn)

        toolbar_layout.addStretch()

        self.selected_count_label = QLabel('已选择: 0 条')
        self.selected_count_label.setStyleSheet('font-size: 14px; color: #666;')
        toolbar_layout.addWidget(self.selected_count_label)

        layout.addLayout(toolbar_layout)

        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(8)
        self.trans_table.setHorizontalHeaderLabels([
            '选择', '日期', '账户', '类型', '分类', '金额', '描述', '操作'
        ])
        self.trans_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.trans_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.trans_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.trans_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.trans_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.trans_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.trans_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.trans_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.trans_table.verticalHeader().setDefaultSectionSize(60)
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
            main_window = self.find_main_window()
            if main_window:
                main_window.update_status_bar()
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
        self.current_transactions = transactions
        self.trans_table.setRowCount(len(transactions))

        for row, trans in enumerate(transactions):
            checkbox = QCheckBox()
            checkbox.setProperty('transaction_id', trans['id'])
            checkbox.setProperty('account_id', trans['account_id'])
            checkbox.setProperty('type', trans['type'])
            checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(r, state))
            
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(10, 0, 0, 0)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.trans_table.setCellWidget(row, 0, checkbox_widget)

            self.trans_table.setItem(row, 1, QTableWidgetItem(trans['date']))
            self.trans_table.setItem(row, 2, QTableWidgetItem(trans['account_name']))

            type_item = QTableWidgetItem('收入' if trans['type'] == 'income' else '支出')
            if trans['type'] == 'income':
                type_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                type_item.setForeground(Qt.GlobalColor.darkRed)
            self.trans_table.setItem(row, 3, type_item)

            self.trans_table.setItem(row, 4, QTableWidgetItem(trans['category_name']))

            amount = trans['amount']
            amount_str = f'+¥ {amount:,.2f}' if trans['type'] == 'income' else f'-¥ {amount:,.2f}'
            amount_item = QTableWidgetItem(amount_str)
            if trans['type'] == 'income':
                amount_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                amount_item.setForeground(Qt.GlobalColor.darkRed)
            self.trans_table.setItem(row, 5, amount_item)

            self.trans_table.setItem(row, 6, QTableWidgetItem(trans['description'] or '-'))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(5)

            split_btn = QPushButton('拆分')
            split_btn.setFixedSize(55, 32)
            split_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4285f4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3367d6;
                }
            """)
            split_btn.clicked.connect(lambda checked, t_id=trans['id']: self.split_transaction(t_id))
            btn_layout.addWidget(split_btn)

            delete_btn = QPushButton('删除')
            delete_btn.setFixedSize(55, 32)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ea4335;
                    color: white;
                    border: none;
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

            self.trans_table.setCellWidget(row, 7, btn_widget)

        self.select_all_check.setChecked(False)
        self.update_selected_count()

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
            '确定要删除这条记录吗？\n记录将被移至回收站，可随时恢复。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_transaction(transaction_id):
                QMessageBox.information(self, '成功', '记录已移至回收站！')
                self.refresh_data()
                main_window = self.find_main_window()
                if main_window:
                    main_window.update_status_bar()
            else:
                QMessageBox.critical(self, '错误', '删除记录失败！')

    def on_select_all_changed(self, state):
        checked = state == Qt.CheckState.Checked
        for row in range(self.trans_table.rowCount()):
            widget = self.trans_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                if checkbox:
                    checkbox.setChecked(checked)
        self.update_selected_count()

    def on_checkbox_changed(self, row, state):
        self.update_selected_count()

    def update_selected_count(self):
        count = 0
        for row in range(self.trans_table.rowCount()):
            widget = self.trans_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                if checkbox and checkbox.isChecked():
                    count += 1
        self.selected_count_label.setText(f'已选择: {count} 条')

    def get_selected_transactions(self):
        selected = []
        for row in range(self.trans_table.rowCount()):
            widget = self.trans_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                if checkbox and checkbox.isChecked():
                    if hasattr(self, 'current_transactions') and row < len(self.current_transactions):
                        selected.append(self.current_transactions[row])
        return selected

    def split_transaction(self, transaction_id):
        dialog = TransactionSplitDialog(self.db, transaction_id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            main_window = self.find_main_window()
            if main_window:
                main_window.update_status_bar()

    def merge_selected_transactions(self):
        selected = self.get_selected_transactions()
        if len(selected) < 2:
            QMessageBox.warning(self, '警告', '请至少选择2条交易进行合并！')
            return

        account_id = selected[0]['account_id']
        type_ = selected[0]['type']
        
        for trans in selected[1:]:
            if trans['account_id'] != account_id:
                QMessageBox.warning(self, '警告', '只能合并同一账户的交易！')
                return
            if trans['type'] != type_:
                QMessageBox.warning(self, '警告', '只能合并相同类型的交易！')
                return

        dialog = TransactionMergeDialog(self.db, selected, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_data()
            main_window = self.find_main_window()
            if main_window:
                main_window.update_status_bar()
