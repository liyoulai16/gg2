from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QDoubleSpinBox,
    QInputDialog, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt


class AccountWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.refresh_data()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.Wheel:
            if isinstance(obj, (QDoubleSpinBox, QSpinBox, QDateEdit)):
                return True
        return super().eventFilter(obj, event)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        add_group = QGroupBox('添加账户')
        add_layout = QHBoxLayout(add_group)

        name_label = QLabel('账户名称:')
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('例如：现金、银行卡、支付宝...')
        add_layout.addWidget(name_label)
        add_layout.addWidget(self.name_edit)

        balance_label = QLabel('初始余额:')
        self.balance_spin = QDoubleSpinBox()
        self.balance_spin.setRange(-999999999, 999999999)
        self.balance_spin.setDecimals(2)
        self.balance_spin.setPrefix('¥ ')
        self.balance_spin.setValue(0)
        self.balance_spin.installEventFilter(self)
        add_layout.addWidget(balance_label)
        add_layout.addWidget(self.balance_spin)

        add_btn = QPushButton('✓ 添加账户')
        add_btn.setMinimumWidth(100)
        add_btn.clicked.connect(self.add_account)
        add_layout.addWidget(add_btn)

        add_layout.addStretch()
        layout.addWidget(add_group)

        stats_group = QGroupBox('账户统计')
        stats_layout = QHBoxLayout(stats_group)

        self.total_balance_label = QLabel('总资产: ¥ 0.00')
        self.total_balance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4285f4;")
        stats_layout.addWidget(self.total_balance_label)

        self.account_count_label = QLabel('账户数量: 0')
        self.account_count_label.setStyleSheet("font-size: 14px; color: #5f6368;")
        stats_layout.addWidget(self.account_count_label)

        stats_layout.addStretch()

        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self.refresh_data)
        stats_layout.addWidget(refresh_btn)

        layout.addWidget(stats_group)

        self.account_table = QTableWidget()
        self.account_table.setColumnCount(5)
        self.account_table.setHorizontalHeaderLabels([
            'ID', '账户名称', '当前余额', '创建时间', '操作'
        ])
        self.account_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.account_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.account_table.verticalHeader().setDefaultSectionSize(60)
        self.account_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.account_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.account_table.setAlternatingRowColors(True)
        layout.addWidget(self.account_table)

    def refresh_data(self):
        accounts = self.db.get_all_accounts()
        self.update_account_table(accounts)
        self.update_stats()

    def update_account_table(self, accounts):
        self.account_table.setRowCount(len(accounts))

        for row, account in enumerate(accounts):
            self.account_table.setItem(row, 0, QTableWidgetItem(str(account['id'])))
            self.account_table.setItem(row, 1, QTableWidgetItem(account['name']))

            balance = account['balance']
            balance_item = QTableWidgetItem(f'¥ {balance:,.2f}')
            if balance >= 0:
                balance_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                balance_item.setForeground(Qt.GlobalColor.darkRed)
            self.account_table.setItem(row, 2, balance_item)

            self.account_table.setItem(row, 3, QTableWidgetItem(account['created_at']))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            edit_btn = QPushButton('编辑')
            edit_btn.setFixedSize(70, 32)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4285f4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3367d6;
                }
            """)
            edit_btn.clicked.connect(lambda checked, a=account: self.edit_account(a))
            btn_layout.addWidget(edit_btn)

            delete_btn = QPushButton('删除')
            delete_btn.setFixedSize(70, 32)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ea4335;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d33427;
                }
            """)
            delete_btn.clicked.connect(lambda checked, a_id=account['id']: self.delete_account(a_id))
            btn_layout.addWidget(delete_btn)

            self.account_table.setCellWidget(row, 4, btn_widget)

    def update_stats(self):
        total_balance = self.db.get_total_balance()
        accounts = self.db.get_all_accounts()

        self.total_balance_label.setText(f'总资产: ¥ {total_balance:,.2f}')
        self.account_count_label.setText(f'账户数量: {len(accounts)}')

    def add_account(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '警告', '请输入账户名称！')
            return

        balance = self.balance_spin.value()

        if self.db.add_account(name, balance):
            QMessageBox.information(self, '成功', f'账户"{name}"添加成功！')
            self.name_edit.clear()
            self.balance_spin.setValue(0)
            self.refresh_data()
            self.parent().parent().update_status_bar()
        else:
            QMessageBox.warning(self, '警告', f'账户名称"{name}"已存在！')

    def edit_account(self, account):
        new_name, ok = QInputDialog.getText(
            self, '编辑账户',
            f'当前账户: {account["name"]}\n\n请输入新的账户名称:',
            text=account['name']
        )

        if ok and new_name.strip():
            if self.db.update_account(account['id'], name=new_name.strip()):
                QMessageBox.information(self, '成功', '账户信息已更新！')
                self.refresh_data()
                self.parent().parent().update_status_bar()
            else:
                QMessageBox.warning(self, '警告', '账户名称已存在或更新失败！')

    def delete_account(self, account_id):
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这个账户吗？\n注意：只有没有交易记录的账户才能删除。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_account(account_id):
                QMessageBox.information(self, '成功', '账户已删除！')
                self.refresh_data()
                self.parent().parent().update_status_bar()
            else:
                QMessageBox.warning(self, '警告', '删除失败！该账户可能有交易记录。')
