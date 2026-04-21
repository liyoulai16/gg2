from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QMessageBox, QDoubleSpinBox,
    QSplitter, QScrollArea, QFrame, QHeaderView,
    QAbstractItemView, QProgressBar, QRadioButton,
    QButtonGroup, QDateEdit, QTextEdit, QInputDialog,
    QTabWidget, QStackedWidget, QFormLayout, QLineEdit
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime


class DebtWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_debt_id = None
        self.init_ui()
        self.refresh_data()

    def eventFilter(self, obj, event):
        if event.type() == event.Type.Wheel:
            if isinstance(obj, (QDoubleSpinBox, QSpinBox)):
                return True
        return super().eventFilter(obj, event)

    def init_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        alert_group = QGroupBox('⚠️ 债务提醒')
        alert_layout = QVBoxLayout(alert_group)
        self.alert_label = QLabel('暂无债务提醒')
        self.alert_label.setStyleSheet("font-size: 14px; color: #5f6368;")
        self.alert_label.setWordWrap(True)
        alert_layout.addWidget(self.alert_label)
        layout.addWidget(alert_group)

        overview_group = QGroupBox('📊 债务概览')
        overview_layout = QVBoxLayout(overview_group)

        stats_layout = QHBoxLayout()

        self.lend_card = self.create_stat_card('借出总额', '#4285f4', 'lend')
        stats_layout.addWidget(self.lend_card)

        self.borrow_card = self.create_stat_card('借入总额', '#ea4335', 'borrow')
        stats_layout.addWidget(self.borrow_card)

        self.completed_lend_card = self.create_stat_card('已结清借出', '#34a853', 'completed_lend')
        stats_layout.addWidget(self.completed_lend_card)

        self.completed_borrow_card = self.create_stat_card('已结清借入', '#fbbc05', 'completed_borrow')
        stats_layout.addWidget(self.completed_borrow_card)

        overview_layout.addLayout(stats_layout)
        layout.addWidget(overview_group)

        main_tab = QTabWidget()

        debt_tab = QWidget()
        debt_tab_layout = QVBoxLayout(debt_tab)
        debt_tab_layout.setSpacing(15)
        debt_tab_layout.setContentsMargins(0, 0, 0, 0)

        add_group = QGroupBox('➕ 添加债务')
        add_layout = QVBoxLayout(add_group)

        type_layout = QHBoxLayout()
        type_label = QLabel('类型:')
        self.type_group = QButtonGroup(self)
        self.lend_radio = QRadioButton('借出 (我借别人)')
        self.borrow_radio = QRadioButton('借入 (别人借我)')
        self.borrow_radio.setChecked(True)
        self.type_group.addButton(self.lend_radio, 0)
        self.type_group.addButton(self.borrow_radio, 1)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.lend_radio)
        type_layout.addWidget(self.borrow_radio)
        type_layout.addStretch()
        add_layout.addLayout(type_layout)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        counterparty_label = QLabel('对方名称:')
        self.counterparty_edit = QLineEdit()
        self.counterparty_edit.setPlaceholderText('例如：张三、李四...')
        form_layout.addRow(counterparty_label, self.counterparty_edit)

        amount_label = QLabel('金额:')
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix('¥ ')
        self.amount_spin.setValue(0)
        self.amount_spin.installEventFilter(self)
        form_layout.addRow(amount_label, self.amount_spin)

        interest_label = QLabel('利率 (%):')
        self.interest_spin = QDoubleSpinBox()
        self.interest_spin.setRange(0, 100)
        self.interest_spin.setDecimals(2)
        self.interest_spin.setValue(0)
        self.interest_spin.installEventFilter(self)
        form_layout.addRow(interest_label, self.interest_spin)

        start_date_label = QLabel('开始日期:')
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.start_date_edit.dateChanged.connect(self.on_start_date_changed)
        form_layout.addRow(start_date_label, self.start_date_edit)

        due_date_label = QLabel('到期日期:')
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate().addDays(30))
        self.due_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.due_date_edit.setSpecialValueText('无到期日')
        self.due_date_edit.setMinimumDate(self.start_date_edit.date())
        form_layout.addRow(due_date_label, self.due_date_edit)

        desc_label = QLabel('备注:')
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText('添加备注信息...')
        self.desc_edit.setMaximumHeight(60)
        form_layout.addRow(desc_label, self.desc_edit)

        add_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton('✓ 添加债务')
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(self.add_debt)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        add_layout.addLayout(btn_layout)

        debt_tab_layout.addWidget(add_group)

        list_group = QGroupBox('📋 债务列表')
        list_layout = QVBoxLayout(list_group)

        filter_layout = QHBoxLayout()
        filter_label = QLabel('筛选:')
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['全部', '进行中', '已结清'])
        self.filter_combo.setFixedWidth(100)
        self.filter_combo.currentIndexChanged.connect(self.refresh_data)

        type_filter_label = QLabel('类型:')
        self.type_filter_combo = QComboBox()
        self.type_filter_combo.addItems(['全部', '借出', '借入'])
        self.type_filter_combo.setFixedWidth(100)
        self.type_filter_combo.currentIndexChanged.connect(self.refresh_data)

        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self.refresh_data)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(type_filter_label)
        filter_layout.addWidget(self.type_filter_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(refresh_btn)
        list_layout.addLayout(filter_layout)

        self.debt_table = QTableWidget()
        self.debt_table.setColumnCount(8)
        self.debt_table.setHorizontalHeaderLabels([
            'ID', '类型', '对方', '总金额', '剩余金额', '到期日', '状态', '操作'
        ])
        self.debt_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.debt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.debt_table.verticalHeader().setDefaultSectionSize(55)
        self.debt_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.debt_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.debt_table.setAlternatingRowColors(True)
        self.debt_table.doubleClicked.connect(self.on_debt_double_clicked)
        list_layout.addWidget(self.debt_table)

        debt_tab_layout.addWidget(list_group)
        main_tab.addTab(debt_tab, '💳 债务管理')

        payment_tab = QWidget()
        payment_tab_layout = QVBoxLayout(payment_tab)
        payment_tab_layout.setSpacing(15)
        payment_tab_layout.setContentsMargins(0, 0, 0, 0)

        self.payment_stack = QStackedWidget()

        no_selection_widget = QWidget()
        no_selection_layout = QVBoxLayout(no_selection_widget)
        no_selection_label = QLabel('👈 请先在"债务管理"标签页中双击选择一个债务')
        no_selection_label.setStyleSheet("font-size: 16px; color: #5f6368;")
        no_selection_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_selection_layout.addWidget(no_selection_label)
        self.payment_stack.addWidget(no_selection_widget)

        payment_detail_widget = QWidget()
        payment_detail_layout = QVBoxLayout(payment_detail_widget)

        self.debt_info_group = QGroupBox('📌 债务信息')
        debt_info_layout = QFormLayout(self.debt_info_group)
        self.debt_info_type = QLabel('-')
        self.debt_info_counterparty = QLabel('-')
        self.debt_info_amount = QLabel('-')
        self.debt_info_remaining = QLabel('-')
        self.debt_info_status = QLabel('-')
        debt_info_layout.addRow('类型:', self.debt_info_type)
        debt_info_layout.addRow('对方:', self.debt_info_counterparty)
        debt_info_layout.addRow('总金额:', self.debt_info_amount)
        debt_info_layout.addRow('剩余金额:', self.debt_info_remaining)
        debt_info_layout.addRow('状态:', self.debt_info_status)
        payment_detail_layout.addWidget(self.debt_info_group)

        add_payment_group = QGroupBox('➕ 添加还款计划')
        add_payment_layout = QFormLayout(add_payment_group)

        payment_amount_label = QLabel('还款金额:')
        self.payment_amount_spin = QDoubleSpinBox()
        self.payment_amount_spin.setRange(0, 999999999)
        self.payment_amount_spin.setDecimals(2)
        self.payment_amount_spin.setPrefix('¥ ')
        self.payment_amount_spin.setValue(0)
        self.payment_amount_spin.installEventFilter(self)
        add_payment_layout.addRow(payment_amount_label, self.payment_amount_spin)

        payment_due_label = QLabel('到期日期:')
        self.payment_due_edit = QDateEdit()
        self.payment_due_edit.setCalendarPopup(True)
        self.payment_due_edit.setDate(QDate.currentDate().addDays(30))
        self.payment_due_edit.setDisplayFormat('yyyy-MM-dd')
        add_payment_layout.addRow(payment_due_label, self.payment_due_edit)

        payment_desc_label = QLabel('备注:')
        self.payment_desc_edit = QLineEdit()
        self.payment_desc_edit.setPlaceholderText('备注信息...')
        add_payment_layout.addRow(payment_desc_label, self.payment_desc_edit)

        add_payment_btn = QPushButton('✓ 添加还款计划')
        add_payment_btn.setMinimumWidth(120)
        add_payment_btn.clicked.connect(self.add_payment_plan)
        add_payment_layout.addRow('', add_payment_btn)

        payment_detail_layout.addWidget(add_payment_group)

        payment_list_group = QGroupBox('📋 还款计划列表')
        payment_list_layout = QVBoxLayout(payment_list_group)

        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(6)
        self.payment_table.setHorizontalHeaderLabels([
            'ID', '金额', '到期日期', '实际还款日期', '状态', '操作'
        ])
        self.payment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.payment_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.payment_table.verticalHeader().setDefaultSectionSize(55)
        self.payment_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.payment_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.payment_table.setAlternatingRowColors(True)
        payment_list_layout.addWidget(self.payment_table)

        payment_detail_layout.addWidget(payment_list_group)
        self.payment_stack.addWidget(payment_detail_widget)

        payment_tab_layout.addWidget(self.payment_stack)
        main_tab.addTab(payment_tab, '📝 还款计划')

        layout.addWidget(main_tab)

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def create_stat_card(self, title, color, card_type):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 13px; color: {color}; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel('¥ 0.00')
        value_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #202124;")
        layout.addWidget(value_label)

        count_label = QLabel('0 笔')
        count_label.setStyleSheet("font-size: 12px; color: #5f6368;")
        layout.addWidget(count_label)

        card.value_label = value_label
        card.count_label = count_label
        card.card_type = card_type
        return card

    def refresh_data(self):
        self.refresh_reminders()
        self.refresh_summary()
        self.refresh_debt_list()
        if self.current_debt_id:
            self.refresh_payment_list()

    def refresh_reminders(self):
        reminders = self.db.get_debt_reminders(7)
        if reminders:
            reminder_messages = []
            for r in reminders:
                reminder_messages.append(r['message'])
            self.alert_label.setText('\n'.join(reminder_messages))
            self.alert_label.setStyleSheet("font-size: 14px; color: #ea4335;")
        else:
            self.alert_label.setText('✅ 暂无即将到期或逾期的债务')
            self.alert_label.setStyleSheet("font-size: 14px; color: #34a853;")

    def refresh_summary(self):
        summary = self.db.get_debt_summary()

        self.lend_card.value_label.setText(f'¥ {summary["lend_active"]["amount"]:,.2f}')
        self.lend_card.count_label.setText(f'{summary["lend_active"]["count"]} 笔')

        self.borrow_card.value_label.setText(f'¥ {summary["borrow_active"]["amount"]:,.2f}')
        self.borrow_card.count_label.setText(f'{summary["borrow_active"]["count"]} 笔')

        self.completed_lend_card.value_label.setText(f'¥ {summary["lend_completed"]["amount"]:,.2f}')
        self.completed_lend_card.count_label.setText(f'{summary["lend_completed"]["count"]} 笔')

        self.completed_borrow_card.value_label.setText(f'¥ {summary["borrow_completed"]["amount"]:,.2f}')
        self.completed_borrow_card.count_label.setText(f'{summary["borrow_completed"]["count"]} 笔')

    def refresh_debt_list(self):
        filter_index = self.filter_combo.currentIndex()
        type_filter_index = self.type_filter_combo.currentIndex()

        status_filter = None
        type_filter = None

        if filter_index == 1:
            status_filter = 'active'
        elif filter_index == 2:
            status_filter = 'completed'

        if type_filter_index == 1:
            type_filter = 'lend'
        elif type_filter_index == 2:
            type_filter = 'borrow'

        if type_filter:
            debts = self.db.get_all_debts(type_=type_filter)
        else:
            debts = self.db.get_all_debts()

        if status_filter:
            debts = [d for d in debts if d['status'] == status_filter]

        self.debt_table.setRowCount(len(debts))

        for row, debt in enumerate(debts):
            self.debt_table.setItem(row, 0, QTableWidgetItem(str(debt['id'])))

            type_label = '借出' if debt['type'] == 'lend' else '借入'
            type_item = QTableWidgetItem(type_label)
            if debt['type'] == 'lend':
                type_item.setForeground(Qt.GlobalColor.darkBlue)
            else:
                type_item.setForeground(Qt.GlobalColor.darkRed)
            self.debt_table.setItem(row, 1, type_item)

            self.debt_table.setItem(row, 2, QTableWidgetItem(debt['counterparty']))

            amount_item = QTableWidgetItem(f'¥ {debt["amount"]:,.2f}')
            self.debt_table.setItem(row, 3, amount_item)

            remaining = debt['remaining_amount']
            remaining_item = QTableWidgetItem(f'¥ {remaining:,.2f}')
            if remaining > 0:
                remaining_item.setForeground(Qt.GlobalColor.darkGreen)
            elif remaining == 0:
                remaining_item.setForeground(Qt.GlobalColor.gray)
            self.debt_table.setItem(row, 4, remaining_item)

            due_date = debt['due_date'] or '无'
            self.debt_table.setItem(row, 5, QTableWidgetItem(due_date))

            status_text = '进行中' if debt['status'] == 'active' else '已结清'
            status_item = QTableWidgetItem(status_text)
            if debt['status'] == 'active':
                status_item.setForeground(Qt.GlobalColor.darkBlue)
            else:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            self.debt_table.setItem(row, 6, status_item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            edit_btn = QPushButton('编辑')
            edit_btn.setFixedSize(80, 32)
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
            edit_btn.clicked.connect(lambda checked, d=debt: self.edit_debt(d))
            btn_layout.addWidget(edit_btn)

            delete_btn = QPushButton('删除')
            delete_btn.setFixedSize(80, 32)
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
            delete_btn.clicked.connect(lambda checked, d_id=debt['id']: self.delete_debt(d_id))
            btn_layout.addWidget(delete_btn)

            self.debt_table.setCellWidget(row, 7, btn_widget)

    def on_start_date_changed(self, new_date):
        self.due_date_edit.setMinimumDate(new_date)
        if self.due_date_edit.date() < new_date:
            self.due_date_edit.setDate(new_date.addDays(30))

    def add_debt(self):
        counterparty = self.counterparty_edit.text().strip()
        if not counterparty:
            QMessageBox.warning(self, '警告', '请输入对方名称！')
            return

        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, '警告', '请输入有效的金额！')
            return

        start_date = self.start_date_edit.date()
        due_date = self.due_date_edit.date()

        if due_date < start_date:
            QMessageBox.warning(self, '警告', '到期日期不能早于开始日期！')
            return

        type_ = 'lend' if self.lend_radio.isChecked() else 'borrow'
        interest_rate = self.interest_spin.value()
        start_date_str = start_date.toString('yyyy-MM-dd')
        due_date_str = due_date.toString('yyyy-MM-dd')
        description = self.desc_edit.toPlainText().strip()

        debt_id = self.db.add_debt(
            type_=type_,
            counterparty=counterparty,
            amount=amount,
            interest_rate=interest_rate,
            start_date=start_date_str,
            due_date=due_date_str,
            description=description
        )

        if debt_id:
            QMessageBox.information(self, '成功', f'债务添加成功！')
            self.clear_debt_form()
            self.refresh_data()
        else:
            QMessageBox.critical(self, '错误', '添加债务失败！')

    def clear_debt_form(self):
        self.counterparty_edit.clear()
        self.amount_spin.setValue(0)
        self.interest_spin.setValue(0)
        self.start_date_edit.setDate(QDate.currentDate())
        self.due_date_edit.setDate(QDate.currentDate().addDays(30))
        self.desc_edit.clear()

    def edit_debt(self, debt):
        new_counterparty, ok = QInputDialog.getText(
            self, '编辑债务',
            f'当前: {debt["counterparty"]}\n请输入新的对方名称:',
            text=debt['counterparty']
        )

        if ok and new_counterparty.strip():
            if self.db.update_debt(debt['id'], counterparty=new_counterparty.strip()):
                QMessageBox.information(self, '成功', '债务信息已更新！')
                self.refresh_data()
            else:
                QMessageBox.warning(self, '警告', '更新失败！')

    def delete_debt(self, debt_id):
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这个债务吗？\n此操作将同时删除所有相关的还款计划。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_debt(debt_id):
                if self.current_debt_id == debt_id:
                    self.current_debt_id = None
                    self.payment_stack.setCurrentIndex(0)
                QMessageBox.information(self, '成功', '债务已删除！')
                self.refresh_data()
            else:
                QMessageBox.critical(self, '错误', '删除失败！')

    def on_debt_double_clicked(self, index):
        row = index.row()
        debt_id_item = self.debt_table.item(row, 0)
        if debt_id_item:
            debt_id = int(debt_id_item.text())
            self.select_debt(debt_id)

    def select_debt(self, debt_id):
        self.current_debt_id = debt_id
        debt = self.db.get_debt(debt_id)

        if debt:
            type_label = '借出' if debt['type'] == 'lend' else '借入'
            self.debt_info_type.setText(type_label)
            self.debt_info_counterparty.setText(debt['counterparty'])
            self.debt_info_amount.setText(f'¥ {debt["amount"]:,.2f}')
            self.debt_info_remaining.setText(f'¥ {debt["remaining_amount"]:,.2f}')
            status_text = '进行中' if debt['status'] == 'active' else '已结清'
            self.debt_info_status.setText(status_text)

            self.payment_stack.setCurrentIndex(1)
            self.refresh_payment_list()

            remaining = debt['remaining_amount']
            self.payment_amount_spin.setRange(0, remaining)
            self.payment_amount_spin.setValue(0)

    def refresh_payment_list(self):
        if not self.current_debt_id:
            return

        payments = self.db.get_debt_payments(self.current_debt_id)
        self.payment_table.setRowCount(len(payments))

        for row, payment in enumerate(payments):
            self.payment_table.setItem(row, 0, QTableWidgetItem(str(payment['id'])))

            amount_item = QTableWidgetItem(f'¥ {payment["amount"]:,.2f}')
            self.payment_table.setItem(row, 1, amount_item)

            self.payment_table.setItem(row, 2, QTableWidgetItem(payment['due_date']))

            paid_date = payment['paid_date'] or '-'
            self.payment_table.setItem(row, 3, QTableWidgetItem(paid_date))

            status_text = '待还款' if payment['status'] == 'pending' else '已还款'
            status_item = QTableWidgetItem(status_text)
            if payment['status'] == 'pending':
                status_item.setForeground(Qt.GlobalColor.darkBlue)
            else:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            self.payment_table.setItem(row, 4, status_item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            if payment['status'] == 'pending':
                pay_btn = QPushButton('标记已还')
                pay_btn.setFixedSize(100, 32)
                pay_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #34a853;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 13px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2d8e47;
                    }
                """)
                pay_btn.clicked.connect(lambda checked, p_id=payment['id']: self.mark_payment_paid(p_id))
                btn_layout.addWidget(pay_btn)

            delete_btn = QPushButton('删除')
            delete_btn.setFixedSize(80, 32)
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
            delete_btn.clicked.connect(lambda checked, p_id=payment['id']: self.delete_payment(p_id))
            btn_layout.addWidget(delete_btn)

            self.payment_table.setCellWidget(row, 5, btn_widget)

    def add_payment_plan(self):
        if not self.current_debt_id:
            QMessageBox.warning(self, '警告', '请先选择一个债务！')
            return

        amount = self.payment_amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, '警告', '请输入有效的还款金额！')
            return

        due_date = self.payment_due_edit.date().toString('yyyy-MM-dd')
        description = self.payment_desc_edit.text().strip()

        payment_id = self.db.add_debt_payment(
            debt_id=self.current_debt_id,
            amount=amount,
            due_date=due_date,
            description=description
        )

        if payment_id:
            QMessageBox.information(self, '成功', '还款计划添加成功！')
            self.payment_amount_spin.setValue(0)
            self.payment_desc_edit.clear()
            self.refresh_data()
        else:
            QMessageBox.critical(self, '错误', '添加还款计划失败！')

    def mark_payment_paid(self, payment_id):
        reply = QMessageBox.question(
            self, '确认还款',
            '确定要将此还款计划标记为已还款吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.mark_payment_paid(payment_id):
                QMessageBox.information(self, '成功', '已标记为已还款！')
                self.refresh_data()
            else:
                QMessageBox.critical(self, '错误', '操作失败！')

    def delete_payment(self, payment_id):
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这个还款计划吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_debt_payment(payment_id):
                QMessageBox.information(self, '成功', '还款计划已删除！')
                self.refresh_data()
            else:
                QMessageBox.critical(self, '错误', '删除失败！')