from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QRadioButton,
    QButtonGroup, QDateEdit, QMessageBox, QDoubleSpinBox,
    QSplitter, QScrollArea, QFrame, QHeaderView,
    QAbstractItemView, QApplication, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, QDate, QTimer
from datetime import datetime


class RecurringWidget(QWidget):
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
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        reminder_group = QGroupBox('🔔 到期提醒')
        reminder_layout = QVBoxLayout(reminder_group)
        self.reminder_label = QLabel('暂无到期的周期性账单')
        self.reminder_label.setStyleSheet("font-size: 14px; color: #5f6368;")
        reminder_layout.addWidget(self.reminder_label)
        layout.addWidget(reminder_group)

        splitter = QSplitter(Qt.Orientation.Vertical)

        add_group = QGroupBox('➕ 添加周期性账单')
        add_layout = QVBoxLayout(add_group)

        type_group = QGroupBox('类型')
        type_layout = QHBoxLayout(type_group)
        self.type_group = QButtonGroup(self)
        self.income_radio = QRadioButton('💰 收入')
        self.expense_radio = QRadioButton('💸 支出')
        self.expense_radio.setChecked(True)
        self.type_group.addButton(self.income_radio)
        self.type_group.addButton(self.expense_radio)
        type_layout.addWidget(self.income_radio)
        type_layout.addWidget(self.expense_radio)
        type_layout.addStretch()
        add_layout.addWidget(type_group)

        self.income_radio.toggled.connect(self.on_type_changed)

        form_layout = QGridLayout()
        form_layout.setSpacing(15)

        name_label = QLabel('名称:')
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('例如：工资、房租、水电')
        self.name_edit.setMinimumWidth(200)
        form_layout.addWidget(name_label, 0, 0)
        form_layout.addWidget(self.name_edit, 0, 1)

        amount_label = QLabel('金额:')
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix('¥ ')
        self.amount_spin.setValue(0)
        self.amount_spin.setMinimumWidth(200)
        self.amount_spin.installEventFilter(self)
        form_layout.addWidget(amount_label, 1, 0)
        form_layout.addWidget(self.amount_spin, 1, 1)

        frequency_label = QLabel('周期:')
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(['每日', '每周', '每月', '每年'])
        self.frequency_combo.setCurrentText('每月')
        self.frequency_combo.setMinimumWidth(100)
        form_layout.addWidget(frequency_label, 1, 2)
        form_layout.addWidget(self.frequency_combo, 1, 3)

        account_label = QLabel('账户:')
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(120)
        form_layout.addWidget(account_label, 0, 2)
        form_layout.addWidget(self.account_combo, 0, 3)

        category_label = QLabel('分类:')
        self.category_combo = QComboBox()
        self.category_combo.setMinimumWidth(120)
        form_layout.addWidget(category_label, 0, 4)
        form_layout.addWidget(self.category_combo, 0, 5)

        start_label = QLabel('开始日期:')
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setMinimumWidth(120)
        self.start_date_edit.installEventFilter(self)
        form_layout.addWidget(start_label, 1, 4)
        form_layout.addWidget(self.start_date_edit, 1, 5)

        end_label = QLabel('结束日期:')
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate().addYears(10))
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setMinimumWidth(120)
        self.end_date_edit.installEventFilter(self)
        form_layout.addWidget(end_label, 2, 4)
        form_layout.addWidget(self.end_date_edit, 2, 5)

        self.end_checkbox = QCheckBox('无结束日期')
        self.end_checkbox.setChecked(False)
        self.end_checkbox.toggled.connect(self.on_end_checkbox_toggled)
        form_layout.addWidget(self.end_checkbox, 2, 6)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText('可选，输入备注信息...')
        self.desc_edit.setMinimumWidth(300)
        form_layout.addWidget(QLabel('描述:'), 2, 0)
        form_layout.addWidget(self.desc_edit, 2, 1)

        self.auto_generate_checkbox = QCheckBox('自动入账')
        self.auto_generate_checkbox.setChecked(True)
        self.auto_generate_checkbox.setToolTip('勾选后到期自动生成交易记录，不勾选则仅提醒')
        form_layout.addWidget(self.auto_generate_checkbox, 2, 2, 1, 2)

        add_btn = QPushButton('✓ 添加周期性账单')
        add_btn.setMinimumWidth(150)
        add_btn.clicked.connect(self.add_recurring_transaction)
        form_layout.addWidget(add_btn, 2, 7)

        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(3, 1)
        form_layout.setColumnStretch(5, 1)
        form_layout.setColumnStretch(7, 1)

        add_layout.addLayout(form_layout)

        splitter.addWidget(add_group)

        list_group = QGroupBox('📋 周期性账单列表')
        list_layout = QVBoxLayout(list_group)

        filter_layout = QHBoxLayout()
        filter_label = QLabel('显示:')
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(['全部', '仅活动', '仅提醒模式'])
        self.filter_combo.currentIndexChanged.connect(self.refresh_data)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)

        generate_btn = QPushButton('🔄 检查并生成到期记录')
        generate_btn.setMinimumWidth(180)
        generate_btn.clicked.connect(self.check_and_generate)
        filter_layout.addWidget(generate_btn)

        filter_layout.addStretch()
        list_layout.addLayout(filter_layout)

        self.recurring_table = QTableWidget()
        self.recurring_table.setColumnCount(11)
        self.recurring_table.setHorizontalHeaderLabels([
            '名称', '类型', '账户', '分类', '金额', '周期',
            '开始日期', '结束日期', '状态', '模式', '操作'
        ])
        self.recurring_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.recurring_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.recurring_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.recurring_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.recurring_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        self.recurring_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        self.recurring_table.verticalHeader().setDefaultSectionSize(60)
        self.recurring_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.recurring_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.recurring_table.setAlternatingRowColors(True)
        list_layout.addWidget(self.recurring_table)

        splitter.addWidget(list_group)
        splitter.setSizes([250, 400])

        layout.addWidget(splitter)

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def on_type_changed(self):
        self.load_categories()

    def on_end_checkbox_toggled(self, checked):
        self.end_date_edit.setEnabled(not checked)

    def load_accounts(self):
        accounts = self.db.get_all_accounts()
        self.account_combo.clear()
        for account in accounts:
            self.account_combo.addItem(f"{account['name']} (¥ {account['balance']:,.2f})", account['id'])

    def load_categories(self):
        type_ = 'income' if self.income_radio.isChecked() else 'expense'
        categories = self.db.get_all_categories(type_)
        self.category_combo.clear()
        for category in categories:
            self.category_combo.addItem(category['name'], category['id'])

    def refresh_data(self):
        self.load_accounts()
        self.load_categories()
        self.load_recurring_list()
        self.load_reminders()

    def load_recurring_list(self):
        filter_text = self.filter_combo.currentText()
        active_only = filter_text == '仅活动'
        all_recurring = self.db.get_all_recurring_transactions(active_only=active_only)
        
        if filter_text == '仅提醒模式':
            all_recurring = [r for r in all_recurring if not r['auto_generate']]

        self.recurring_table.setRowCount(len(all_recurring))

        for row, recurring in enumerate(all_recurring):
            self.recurring_table.setItem(row, 0, QTableWidgetItem(recurring['name']))

            type_item = QTableWidgetItem('收入' if recurring['type'] == 'income' else '支出')
            if recurring['type'] == 'income':
                type_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                type_item.setForeground(Qt.GlobalColor.darkRed)
            self.recurring_table.setItem(row, 1, type_item)

            self.recurring_table.setItem(row, 2, QTableWidgetItem(recurring['account_name']))
            self.recurring_table.setItem(row, 3, QTableWidgetItem(recurring['category_name']))

            amount = recurring['amount']
            amount_str = f'¥ {amount:,.2f}'
            amount_item = QTableWidgetItem(amount_str)
            if recurring['type'] == 'income':
                amount_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                amount_item.setForeground(Qt.GlobalColor.darkRed)
            self.recurring_table.setItem(row, 4, amount_item)

            frequency_map = {'daily': '每日', 'weekly': '每周', 'monthly': '每月', 'yearly': '每年'}
            self.recurring_table.setItem(row, 5, QTableWidgetItem(frequency_map.get(recurring['frequency'], recurring['frequency'])))
            self.recurring_table.setItem(row, 6, QTableWidgetItem(recurring['start_date']))
            self.recurring_table.setItem(row, 7, QTableWidgetItem(recurring['end_date'] or '无'))

            status_item = QTableWidgetItem('活动' if recurring['is_active'] else '暂停')
            if recurring['is_active']:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                status_item.setForeground(Qt.GlobalColor.darkRed)
            self.recurring_table.setItem(row, 8, status_item)

            mode_item = QTableWidgetItem('自动入账' if recurring['auto_generate'] else '仅提醒')
            if recurring['auto_generate']:
                mode_item.setForeground(Qt.GlobalColor.darkBlue)
            else:
                mode_item.setForeground(Qt.GlobalColor.darkYellow)
            self.recurring_table.setItem(row, 9, mode_item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            if recurring['is_active']:
                pause_btn = QPushButton('暂停')
                pause_btn.setFixedSize(60, 32)
                pause_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #fbbc05;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #f9ab00;
                    }
                """)
                pause_btn.clicked.connect(lambda checked, rid=recurring['id']: self.toggle_recurring(rid, False))
                btn_layout.addWidget(pause_btn)
            else:
                resume_btn = QPushButton('恢复')
                resume_btn.setFixedSize(60, 32)
                resume_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #34a853;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #2d8e47;
                    }
                """)
                resume_btn.clicked.connect(lambda checked, rid=recurring['id']: self.toggle_recurring(rid, True))
                btn_layout.addWidget(resume_btn)

            delete_btn = QPushButton('删除')
            delete_btn.setFixedSize(60, 32)
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
            delete_btn.clicked.connect(lambda checked, rid=recurring['id']: self.delete_recurring(rid))
            btn_layout.addWidget(delete_btn)

            self.recurring_table.setCellWidget(row, 10, btn_widget)

    def load_reminders(self):
        reminders = self.db.get_recurring_reminders(days_ahead=7)
        if reminders:
            reminder_messages = []
            for reminder in reminders:
                if reminder['auto_generate']:
                    icon = '🔔'
                else:
                    icon = '⏰'
                reminder_messages.append(f"{icon} {reminder['message']}")
            self.reminder_label.setText('\n'.join(reminder_messages))
            self.reminder_label.setStyleSheet("font-size: 14px; color: #ea4335;")
        else:
            self.reminder_label.setText('✅ 未来7天内没有到期的周期性账单')
            self.reminder_label.setStyleSheet("font-size: 14px; color: #34a853;")

    def add_recurring_transaction(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '警告', '请输入周期性账单名称！')
            return

        account_id = self.account_combo.currentData()
        if account_id is None:
            QMessageBox.warning(self, '警告', '请选择账户！')
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
        
        frequency_map = {'每日': 'daily', '每周': 'weekly', '每月': 'monthly', '每年': 'yearly'}
        frequency = frequency_map.get(self.frequency_combo.currentText(), 'monthly')
        
        start_date = self.start_date_edit.date().toString('yyyy-MM-dd')
        
        end_date = None
        if not self.end_checkbox.isChecked():
            end_date = self.end_date_edit.date().toString('yyyy-MM-dd')
        
        auto_generate = self.auto_generate_checkbox.isChecked()

        if self.db.add_recurring_transaction(
            name=name,
            type_=type_,
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            description=description,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            auto_generate=auto_generate
        ):
            QMessageBox.information(self, '成功', '周期性账单添加成功！')
            self.name_edit.clear()
            self.amount_spin.setValue(0)
            self.desc_edit.clear()
            self.refresh_data()
        else:
            QMessageBox.critical(self, '错误', '添加周期性账单失败！')

    def toggle_recurring(self, recurring_id, is_active):
        if self.db.update_recurring_transaction(recurring_id, is_active=is_active):
            self.refresh_data()
        else:
            QMessageBox.critical(self, '错误', '操作失败！')

    def delete_recurring(self, recurring_id):
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这个周期性账单吗？\n此操作不会影响已生成的交易记录。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_recurring_transaction(recurring_id):
                QMessageBox.information(self, '成功', '周期性账单已删除！')
                self.refresh_data()
            else:
                QMessageBox.critical(self, '错误', '删除失败！')

    def check_and_generate(self):
        result = self.db.generate_due_recurring_transactions()
        generated = result['generated']
        reminders = result['reminders']

        self.refresh_data()

        messages = []
        if generated:
            messages.append(f'✅ 已自动生成 {len(generated)} 条交易记录：')
            for g in generated:
                type_label = '收入' if g['type'] == 'income' else '支出'
                messages.append(f'  - {g["recurring_name"]} ({type_label}): ¥{g["amount"]:,.2f} @ {g["date"]}')
        
        if reminders:
            if messages:
                messages.append('')
            messages.append(f'⏰ 有 {len(reminders)} 条账单仅设置为提醒模式：')
            for r in reminders:
                type_label = '收入' if r['type'] == 'income' else '支出'
                messages.append(f'  - {r["recurring_name"]} ({type_label}): ¥{r["amount"]:,.2f} @ {r["date"]}')

        if not messages:
            messages.append('没有到期的周期性账单需要处理。')

        QMessageBox.information(self, '处理结果', '\n'.join(messages))