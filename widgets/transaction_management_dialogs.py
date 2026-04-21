from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QDoubleSpinBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QMessageBox, QWidget, QHeaderView,
    QAbstractItemView, QCheckBox, QSpinBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime


class TransactionSplitDialog(QDialog):
    def __init__(self, db, transaction_id, parent=None):
        super().__init__(parent)
        self.db = db
        self.transaction_id = transaction_id
        self.transaction = self.db.get_transaction_by_id(transaction_id)
        self.split_items = []
        
        if not self.transaction:
            QMessageBox.critical(self, '错误', '交易不存在！')
            self.reject()
            return
        
        self.setWindowTitle('拆分交易')
        self.setMinimumSize(700, 550)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title_label = QLabel('✂️ 拆分交易')
        title_label.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        info_group = QGroupBox('原交易信息')
        info_layout = QHBoxLayout(info_group)
        
        info_text = f"""
        <table style="font-size: 14px;">
        <tr><td><b>日期:</b></td><td>{self.transaction['date']}</td>
        <td style="padding-left: 30px;"><b>账户:</b></td><td>{self.transaction['account_name']}</td></tr>
        <tr><td><b>类型:</b></td><td>{'收入' if self.transaction['type'] == 'income' else '支出'}</td>
        <td style="padding-left: 30px;"><b>分类:</b></td><td>{self.transaction['category_name']}</td></tr>
        <tr><td><b>金额:</b></td><td style="color: {'#34a853' if self.transaction['type'] == 'income' else '#ea4335'}; font-weight: bold;">
            ¥ {self.transaction['amount']:,.2f}</td>
        <td style="padding-left: 30px;"><b>描述:</b></td><td>{self.transaction['description'] or '-'}</td></tr>
        </table>
        """
        info_label = QLabel(info_text)
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)

        split_group = QGroupBox('拆分明细')
        split_layout = QVBoxLayout(split_group)

        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel('分类:'))
        
        self.new_category_combo = QComboBox()
        categories = self.db.get_all_categories(self.transaction['type'])
        for cat in categories:
            self.new_category_combo.addItem(cat['name'], cat['id'])
        add_layout.addWidget(self.new_category_combo)

        add_layout.addWidget(QLabel('金额:'))
        self.new_amount_spin = QDoubleSpinBox()
        self.new_amount_spin.setRange(0.01, self.transaction['amount'])
        self.new_amount_spin.setDecimals(2)
        self.new_amount_spin.setPrefix('¥ ')
        add_layout.addWidget(self.new_amount_spin)

        add_layout.addWidget(QLabel('描述:'))
        self.new_desc_edit = QLineEdit()
        self.new_desc_edit.setPlaceholderText('可选')
        add_layout.addWidget(self.new_desc_edit)

        add_btn = QPushButton('+ 添加')
        add_btn.setMinimumWidth(80)
        add_btn.setStyleSheet("""
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
        add_btn.clicked.connect(self.add_split_item)
        add_layout.addWidget(add_btn)

        split_layout.addLayout(add_layout)

        self.split_table = QTableWidget()
        self.split_table.setColumnCount(4)
        self.split_table.setHorizontalHeaderLabels(['分类', '金额', '描述', '操作'])
        self.split_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.split_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.split_table.verticalHeader().setDefaultSectionSize(45)
        self.split_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.split_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.split_table.setAlternatingRowColors(True)
        split_layout.addWidget(self.split_table)

        status_layout = QHBoxLayout()
        self.total_label = QLabel('已分配: ¥ 0.00 / ¥ {:.2f}'.format(self.transaction['amount']))
        self.total_label.setStyleSheet('font-size: 14px; font-weight: bold;')
        status_layout.addWidget(self.total_label)
        
        self.remaining_label = QLabel('剩余: ¥ {:.2f}'.format(self.transaction['amount']))
        self.remaining_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #34a853;')
        status_layout.addWidget(self.remaining_label)
        status_layout.addStretch()
        
        split_layout.addLayout(status_layout)
        layout.addWidget(split_group)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton('取消')
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        split_btn = QPushButton('✓ 确认拆分')
        split_btn.setMinimumWidth(120)
        split_btn.setStyleSheet("""
            QPushButton {
                background-color: #34a853;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d8e47;
            }
        """)
        split_btn.clicked.connect(self.do_split)
        button_layout.addWidget(split_btn)

        layout.addLayout(button_layout)
        self.update_status()
    
    def add_split_item(self):
        category_id = self.new_category_combo.currentData()
        category_name = self.new_category_combo.currentText()
        amount = self.new_amount_spin.value()
        description = self.new_desc_edit.text().strip()

        if amount <= 0:
            QMessageBox.warning(self, '警告', '请输入有效的金额！')
            return

        total_allocated = sum(item['amount'] for item in self.split_items)
        if total_allocated + amount > self.transaction['amount'] + 0.01:
            QMessageBox.warning(self, '警告', '拆分金额不能超过原交易金额！')
            return

        self.split_items.append({
            'category_id': category_id,
            'category_name': category_name,
            'amount': amount,
            'description': description
        })

        self.new_amount_spin.setValue(0)
        self.new_desc_edit.clear()
        self.refresh_split_table()
        self.update_status()
    
    def refresh_split_table(self):
        self.split_table.setRowCount(len(self.split_items))

        for row, item in enumerate(self.split_items):
            self.split_table.setItem(row, 0, QTableWidgetItem(item['category_name']))
            
            amount_str = '¥ {:.2f}'.format(item['amount'])
            amount_item = QTableWidgetItem(amount_str)
            if self.transaction['type'] == 'income':
                amount_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                amount_item.setForeground(Qt.GlobalColor.darkRed)
            self.split_table.setItem(row, 1, amount_item)
            
            self.split_table.setItem(row, 2, QTableWidgetItem(item['description'] or '-'))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(5)

            delete_btn = QPushButton('删除')
            delete_btn.setFixedSize(60, 28)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ea4335;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #d33427;
                }
            """)
            delete_btn.clicked.connect(lambda checked, r=row: self.remove_split_item(r))
            btn_layout.addWidget(delete_btn)

            self.split_table.setCellWidget(row, 3, btn_widget)
    
    def remove_split_item(self, row):
        if 0 <= row < len(self.split_items):
            del self.split_items[row]
            self.refresh_split_table()
            self.update_status()
    
    def update_status(self):
        total_allocated = sum(item['amount'] for item in self.split_items)
        remaining = self.transaction['amount'] - total_allocated

        self.total_label.setText('已分配: ¥ {:.2f} / ¥ {:.2f}'.format(total_allocated, self.transaction['amount']))
        
        if abs(remaining) < 0.01:
            self.remaining_label.setText('剩余: ¥ 0.00')
            self.remaining_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #34a853;')
        else:
            self.remaining_label.setText('剩余: ¥ {:.2f}'.format(remaining))
            self.remaining_label.setStyleSheet('font-size: 14px; font-weight: bold; color: #ea4335;')
    
    def do_split(self):
        total_allocated = sum(item['amount'] for item in self.split_items)
        
        if not self.split_items:
            QMessageBox.warning(self, '警告', '请至少添加一个拆分项！')
            return

        if abs(total_allocated - self.transaction['amount']) > 0.01:
            QMessageBox.warning(self, '警告', '拆分金额总和必须等于原交易金额！')
            return

        reply = QMessageBox.question(
            self, '确认拆分',
            f'确定要拆分这条交易吗？\n原交易将被标记为已删除，并创建 {len(self.split_items)} 条新交易。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.db.split_transaction(self.transaction_id, self.split_items)
            if success:
                QMessageBox.information(self, '成功', message)
                self.accept()
            else:
                QMessageBox.critical(self, '错误', message)


class TransactionMergeDialog(QDialog):
    def __init__(self, db, selected_transactions, parent=None):
        super().__init__(parent)
        self.db = db
        self.selected_transactions = selected_transactions
        self.merged_amount = sum(t['amount'] for t in selected_transactions)
        self.first_transaction = selected_transactions[0] if selected_transactions else None
        
        if not self.selected_transactions or len(self.selected_transactions) < 2:
            QMessageBox.critical(self, '错误', '至少需要选择2条交易才能合并！')
            self.reject()
            return
        
        self.setWindowTitle('合并交易')
        self.setMinimumSize(600, 500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        title_label = QLabel('🔗 合并交易')
        title_label.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        info_group = QGroupBox('选中的交易')
        info_layout = QVBoxLayout(info_group)

        info_text = f"""
        <table style="font-size: 14px; width: 100%;">
        <tr><td><b>账户:</b></td><td>{self.first_transaction['account_name']}</td>
        <td style="padding-left: 30px;"><b>类型:</b></td><td>{'收入' if self.first_transaction['type'] == 'income' else '支出'}</td></tr>
        <tr><td><b>交易数量:</b></td><td>{len(self.selected_transactions)} 条</td>
        <td style="padding-left: 30px;"><b>总金额:</b></td>
        <td style="color: {'#34a853' if self.first_transaction['type'] == 'income' else '#ea4335'}; font-weight: bold;">
            ¥ {self.merged_amount:,.2f}</td></tr>
        </table>
        """
        info_label = QLabel(info_text)
        info_layout.addWidget(info_label)

        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(5)
        self.trans_table.setHorizontalHeaderLabels(['日期', '分类', '金额', '描述', ''])
        self.trans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.trans_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.trans_table.verticalHeader().setDefaultSectionSize(40)
        self.trans_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.trans_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.trans_table.setAlternatingRowColors(True)
        self.trans_table.setMaximumHeight(150)
        
        self.trans_table.setRowCount(len(self.selected_transactions))
        for row, trans in enumerate(self.selected_transactions):
            self.trans_table.setItem(row, 0, QTableWidgetItem(trans['date']))
            self.trans_table.setItem(row, 1, QTableWidgetItem(trans['category_name']))
            
            amount_str = '¥ {:.2f}'.format(trans['amount'])
            amount_item = QTableWidgetItem(amount_str)
            if trans['type'] == 'income':
                amount_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                amount_item.setForeground(Qt.GlobalColor.darkRed)
            self.trans_table.setItem(row, 2, amount_item)
            
            self.trans_table.setItem(row, 3, QTableWidgetItem(trans['description'] or '-'))

        info_layout.addWidget(self.trans_table)
        layout.addWidget(info_group)

        merge_group = QGroupBox('合并设置')
        merge_layout = QVBoxLayout(merge_group)

        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel('合并后分类:'))
        
        self.category_combo = QComboBox()
        categories = self.db.get_all_categories(self.first_transaction['type'])
        default_index = 0
        for i, cat in enumerate(categories):
            self.category_combo.addItem(cat['name'], cat['id'])
            if cat['id'] == self.first_transaction['category_id']:
                default_index = i
        self.category_combo.setCurrentIndex(default_index)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        merge_layout.addLayout(category_layout)

        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel('合并后描述:'))
        
        self.desc_edit = QLineEdit()
        default_desc = f"合并自 {len(self.selected_transactions)} 条交易"
        self.desc_edit.setText(default_desc)
        desc_layout.addWidget(self.desc_edit)
        merge_layout.addLayout(desc_layout)

        merge_layout.addWidget(QLabel('<span style="color: #666; font-size: 12px;">注意：合并后原交易将被标记为已删除，并创建一条新的合并交易。</span>'))

        layout.addWidget(merge_group)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton('取消')
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        merge_btn = QPushButton('✓ 确认合并')
        merge_btn.setMinimumWidth(120)
        merge_btn.setStyleSheet("""
            QPushButton {
                background-color: #34a853;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2d8e47;
            }
        """)
        merge_btn.clicked.connect(self.do_merge)
        button_layout.addWidget(merge_btn)

        layout.addLayout(button_layout)
    
    def do_merge(self):
        transaction_ids = [t['id'] for t in self.selected_transactions]
        category_id = self.category_combo.currentData()
        description = self.desc_edit.text().strip()

        reply = QMessageBox.question(
            self, '确认合并',
            f'确定要合并这 {len(self.selected_transactions)} 条交易吗？\n总金额: ¥ {self.merged_amount:,.2f}',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.db.merge_transactions(transaction_ids, category_id, description)
            if success:
                QMessageBox.information(self, '成功', message)
                self.accept()
            else:
                QMessageBox.critical(self, '错误', message)


class TrashWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.refresh_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        header_layout = QHBoxLayout()
        
        title_label = QLabel('🗑️ 账单回收站')
        title_label.setFont(QFont('Microsoft YaHei', 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()

        self.stats_label = QLabel('已删除记录: 0 条')
        self.stats_label.setStyleSheet('font-size: 14px; color: #666;')
        header_layout.addWidget(self.stats_label)

        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.setMinimumWidth(80)
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)

        clear_all_btn = QPushButton('清空回收站')
        clear_all_btn.setMinimumWidth(100)
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ea4335;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d33427;
            }
        """)
        clear_all_btn.clicked.connect(self.clear_all)
        header_layout.addWidget(clear_all_btn)

        layout.addLayout(header_layout)

        self.trash_table = QTableWidget()
        self.trash_table.setColumnCount(8)
        self.trash_table.setHorizontalHeaderLabels(['选择', '日期', '账户', '类型', '分类', '金额', '删除时间', '操作'])
        self.trash_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.trash_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.trash_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.trash_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.trash_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.trash_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.trash_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.trash_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.trash_table.verticalHeader().setDefaultSectionSize(50)
        self.trash_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.trash_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.trash_table.setAlternatingRowColors(True)
        layout.addWidget(self.trash_table)

        batch_layout = QHBoxLayout()
        
        self.select_all_check = QCheckBox('全选')
        self.select_all_check.stateChanged.connect(self.on_select_all_changed)
        batch_layout.addWidget(self.select_all_check)

        batch_layout.addSpacing(20)

        restore_selected_btn = QPushButton('批量恢复')
        restore_selected_btn.setMinimumWidth(100)
        restore_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
        """)
        restore_selected_btn.clicked.connect(self.restore_selected)
        batch_layout.addWidget(restore_selected_btn)

        delete_selected_btn = QPushButton('批量永久删除')
        delete_selected_btn.setMinimumWidth(120)
        delete_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #ea4335;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d33427;
            }
        """)
        delete_selected_btn.clicked.connect(self.delete_selected_permanently)
        batch_layout.addWidget(delete_selected_btn)

        batch_layout.addStretch()
        layout.addLayout(batch_layout)
    
    def refresh_data(self):
        deleted_transactions = self.db.get_deleted_transactions()
        deleted_transactions = [t for t in deleted_transactions if t.get('is_deleted', False)]
        
        self.trash_table.setRowCount(len(deleted_transactions))
        self.stats_label.setText(f'已删除记录: {len(deleted_transactions)} 条')

        for row, trans in enumerate(deleted_transactions):
            checkbox = QCheckBox()
            checkbox.setProperty('transaction_id', trans['id'])
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(10, 0, 0, 0)
            checkbox_layout.addWidget(checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.trash_table.setCellWidget(row, 0, checkbox_widget)

            self.trash_table.setItem(row, 1, QTableWidgetItem(trans['date']))
            self.trash_table.setItem(row, 2, QTableWidgetItem(trans['account_name']))

            type_item = QTableWidgetItem('收入' if trans['type'] == 'income' else '支出')
            if trans['type'] == 'income':
                type_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                type_item.setForeground(Qt.GlobalColor.darkRed)
            self.trash_table.setItem(row, 3, type_item)

            self.trash_table.setItem(row, 4, QTableWidgetItem(trans['category_name']))

            amount_str = '¥ {:.2f}'.format(trans['amount'])
            amount_item = QTableWidgetItem(amount_str)
            if trans['type'] == 'income':
                amount_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                amount_item.setForeground(Qt.GlobalColor.darkRed)
            self.trash_table.setItem(row, 5, amount_item)

            deleted_at = trans.get('deleted_at', '-') or '-'
            self.trash_table.setItem(row, 6, QTableWidgetItem(deleted_at))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            restore_btn = QPushButton('恢复')
            restore_btn.setFixedSize(60, 32)
            restore_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4285f4;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #3367d6;
                }
            """)
            restore_btn.clicked.connect(lambda checked, t_id=trans['id']: self.restore_transaction(t_id))
            btn_layout.addWidget(restore_btn)

            delete_btn = QPushButton('永久删除')
            delete_btn.setFixedSize(80, 32)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ea4335;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #d33427;
                }
            """)
            delete_btn.clicked.connect(lambda checked, t_id=trans['id']: self.delete_permanently(t_id))
            btn_layout.addWidget(delete_btn)

            self.trash_table.setCellWidget(row, 7, btn_widget)

        self.select_all_check.setChecked(False)
    
    def on_select_all_changed(self, state):
        checked = state == Qt.CheckState.Checked
        for row in range(self.trash_table.rowCount()):
            widget = self.trash_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                if checkbox:
                    checkbox.setChecked(checked)
    
    def get_selected_transaction_ids(self):
        selected_ids = []
        for row in range(self.trash_table.rowCount()):
            widget = self.trash_table.cellWidget(row, 0)
            if widget:
                checkbox = widget.layout().itemAt(0).widget()
                if checkbox and checkbox.isChecked():
                    trans_id = checkbox.property('transaction_id')
                    if trans_id:
                        selected_ids.append(trans_id)
        return selected_ids
    
    def restore_transaction(self, transaction_id):
        reply = QMessageBox.question(
            self, '确认恢复',
            '确定要恢复这条交易吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.restore_transaction(transaction_id):
                QMessageBox.information(self, '成功', '交易已恢复！')
                self.refresh_data()
            else:
                QMessageBox.critical(self, '错误', '恢复失败！')
    
    def delete_permanently(self, transaction_id):
        reply = QMessageBox.question(
            self, '确认永久删除',
            '确定要永久删除这条交易吗？此操作不可恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.permanently_delete_transaction(transaction_id):
                QMessageBox.information(self, '成功', '交易已永久删除！')
                self.refresh_data()
            else:
                QMessageBox.critical(self, '错误', '删除失败！')
    
    def restore_selected(self):
        selected_ids = self.get_selected_transaction_ids()
        if not selected_ids:
            QMessageBox.warning(self, '警告', '请先选择要恢复的交易！')
            return

        reply = QMessageBox.question(
            self, '确认批量恢复',
            f'确定要恢复选中的 {len(selected_ids)} 条交易吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            for trans_id in selected_ids:
                if self.db.restore_transaction(trans_id):
                    success_count += 1

            QMessageBox.information(self, '完成', f'已成功恢复 {success_count} 条交易！')
            self.refresh_data()
    
    def delete_selected_permanently(self):
        selected_ids = self.get_selected_transaction_ids()
        if not selected_ids:
            QMessageBox.warning(self, '警告', '请先选择要删除的交易！')
            return

        reply = QMessageBox.question(
            self, '确认批量永久删除',
            f'确定要永久删除选中的 {len(selected_ids)} 条交易吗？此操作不可恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            for trans_id in selected_ids:
                if self.db.permanently_delete_transaction(trans_id):
                    success_count += 1

            QMessageBox.information(self, '完成', f'已成功永久删除 {success_count} 条交易！')
            self.refresh_data()
    
    def clear_all(self):
        deleted_transactions = self.db.get_deleted_transactions()
        deleted_transactions = [t for t in deleted_transactions if t.get('is_deleted', False)]

        if not deleted_transactions:
            QMessageBox.information(self, '提示', '回收站是空的！')
            return

        reply = QMessageBox.question(
            self, '确认清空',
            f'确定要清空回收站吗？将永久删除 {len(deleted_transactions)} 条记录，此操作不可恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success_count = 0
            for trans in deleted_transactions:
                if self.db.permanently_delete_transaction(trans['id']):
                    success_count += 1

            QMessageBox.information(self, '完成', f'已清空回收站！共永久删除 {success_count} 条记录。')
            self.refresh_data()
