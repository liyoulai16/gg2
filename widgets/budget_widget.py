from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QMessageBox, QDoubleSpinBox,
    QSplitter, QScrollArea, QFrame, QHeaderView,
    QAbstractItemView, QProgressBar
)
from PyQt6.QtCore import Qt
from datetime import datetime


class BudgetWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        alert_group = QGroupBox('⚠️ 预算提醒')
        alert_layout = QVBoxLayout(alert_group)
        self.alert_label = QLabel('暂无预算提醒')
        self.alert_label.setStyleSheet("font-size: 14px; color: #5f6368;")
        alert_layout.addWidget(self.alert_label)
        layout.addWidget(alert_group)

        overview_group = QGroupBox('📊 预算概览')
        overview_layout = QVBoxLayout(overview_group)

        period_layout = QHBoxLayout()
        period_label = QLabel('月份:')
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(datetime.now().year)
        self.year_spin.setFixedHeight(36)
        self.year_spin.valueChanged.connect(self.refresh_data)

        self.month_combo = QComboBox()
        for m in range(1, 13):
            self.month_combo.addItem(f'{m}月', m)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        self.month_combo.setFixedHeight(36)
        self.month_combo.currentIndexChanged.connect(self.refresh_data)

        period_layout.addWidget(period_label)
        period_layout.addWidget(self.year_spin)
        period_layout.addWidget(self.month_combo)
        period_layout.addStretch()
        overview_layout.addLayout(period_layout)

        stats_layout = QHBoxLayout()

        self.budget_card = self.create_stat_card('预算金额', '#4285f4')
        stats_layout.addWidget(self.budget_card)

        self.spent_card = self.create_stat_card('已支出', '#ea4335')
        stats_layout.addWidget(self.spent_card)

        self.remaining_card = self.create_stat_card('剩余金额', '#34a853')
        stats_layout.addWidget(self.remaining_card)

        self.percent_card = self.create_stat_card('使用比例', '#fbbc05')
        stats_layout.addWidget(self.percent_card)

        overview_layout.addLayout(stats_layout)

        progress_layout = QVBoxLayout()
        progress_label = QLabel('预算进度:')
        progress_layout.addWidget(progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4285f4;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        overview_layout.addLayout(progress_layout)

        layout.addWidget(overview_group)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        budget_group = QGroupBox('💰 月度预算设置')
        budget_layout = QVBoxLayout(budget_group)

        set_layout = QHBoxLayout()
        amount_label = QLabel('预算金额:')
        self.budget_spin = QDoubleSpinBox()
        self.budget_spin.setRange(0, 999999999)
        self.budget_spin.setDecimals(2)
        self.budget_spin.setPrefix('¥ ')
        self.budget_spin.setFixedHeight(36)
        set_btn = QPushButton('✓ 设置预算')
        set_btn.setFixedHeight(36)
        set_btn.clicked.connect(self.set_monthly_budget)

        set_layout.addWidget(amount_label)
        set_layout.addWidget(self.budget_spin)
        set_layout.addWidget(set_btn)
        budget_layout.addLayout(set_layout)

        self.budget_table = QTableWidget()
        self.budget_table.setColumnCount(4)
        self.budget_table.setHorizontalHeaderLabels(['年份', '月份', '预算金额', '操作'])
        self.budget_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.budget_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.budget_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.budget_table.verticalHeader().setDefaultSectionSize(60)
        self.budget_table.horizontalHeader().setDefaultSectionSize(60)
        self.budget_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.budget_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.budget_table.setAlternatingRowColors(True)
        self.budget_table.setMinimumHeight(200)
        budget_layout.addWidget(self.budget_table)

        splitter.addWidget(budget_group)

        category_group = QGroupBox('📁 分类子预算')
        category_layout = QVBoxLayout(category_group)

        cat_set_layout = QHBoxLayout()
        cat_label = QLabel('分类:')
        self.category_combo = QComboBox()
        self.category_combo.setFixedHeight(36)

        cat_amount_label = QLabel('预算金额:')
        self.cat_budget_spin = QDoubleSpinBox()
        self.cat_budget_spin.setRange(0, 999999999)
        self.cat_budget_spin.setDecimals(2)
        self.cat_budget_spin.setPrefix('¥ ')
        self.cat_budget_spin.setFixedHeight(36)

        cat_set_btn = QPushButton('✓ 设置')
        cat_set_btn.setFixedHeight(36)
        cat_set_btn.clicked.connect(self.set_category_budget)

        cat_set_layout.addWidget(cat_label)
        cat_set_layout.addWidget(self.category_combo)
        cat_set_layout.addWidget(cat_amount_label)
        cat_set_layout.addWidget(self.cat_budget_spin)
        cat_set_layout.addWidget(cat_set_btn)
        category_layout.addLayout(cat_set_layout)

        self.category_table = QTableWidget()
        self.category_table.setColumnCount(6)
        self.category_table.setHorizontalHeaderLabels(['分类', '预算金额', '已支出', '剩余', '进度', '操作'])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.category_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.category_table.verticalHeader().setDefaultSectionSize(65)
        self.category_table.horizontalHeader().setDefaultSectionSize(65)
        self.category_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.category_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setMinimumHeight(250)
        category_layout.addWidget(self.category_table)

        splitter.addWidget(category_group)

        splitter.setSizes([400, 600])
        layout.addWidget(splitter)

        scroll_area.setWidget(content_widget)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def create_stat_card(self, title, color):
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

        card.value_label = value_label
        return card

    def refresh_data(self):
        year = self.year_spin.value()
        month = self.month_combo.currentData()

        budget = self.db.get_budget(year, month)
        if budget:
            self.budget_spin.setValue(budget['amount'])

        usage = self.db.get_budget_usage(year, month)

        self.budget_card.value_label.setText(f'¥ {usage["budget_amount"]:,.2f}')
        self.spent_card.value_label.setText(f'¥ {usage["spent_amount"]:,.2f}')
        self.remaining_card.value_label.setText(f'¥ {usage["remaining"]:,.2f}')
        self.percent_card.value_label.setText(f'{usage["percentage"]:.1f}%')

        if usage["budget_amount"] > 0:
            self.progress_bar.setValue(int(min(usage["percentage"], 100)))
            if usage["percentage"] >= 100:
                self.progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #ea4335;
                        border-radius: 3px;
                    }
                """)
            elif usage["percentage"] >= 80:
                self.progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #fbbc05;
                        border-radius: 3px;
                    }
                """)
            else:
                self.progress_bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                        text-align: center;
                    }
                    QProgressBar::chunk {
                        background-color: #34a853;
                        border-radius: 3px;
                    }
                """)
        else:
            self.progress_bar.setValue(0)

        alerts = self.db.check_over_budget(year, month)
        if alerts:
            alert_messages = []
            for alert in alerts:
                if alert['type'] == 'total_over':
                    alert_messages.append(f'🔴 {alert["message"]}')
                elif alert['type'] == 'total_warning':
                    alert_messages.append(f'🟡 {alert["message"]}')
                elif alert['type'] == 'category_over':
                    alert_messages.append(f'🔴 {alert["message"]}')
                elif alert['type'] == 'category_warning':
                    alert_messages.append(f'🟡 {alert["message"]}')
            self.alert_label.setText('\n'.join(alert_messages))
            self.alert_label.setStyleSheet("font-size: 14px; color: #ea4335;")
        else:
            self.alert_label.setText('✅ 预算使用情况良好，暂无超支提醒')
            self.alert_label.setStyleSheet("font-size: 14px; color: #34a853;")

        self.load_budget_history()
        self.load_categories()
        self.load_category_budgets(usage)

    def load_budget_history(self):
        budgets = self.db.get_all_budgets()
        self.budget_table.setRowCount(len(budgets))

        for row, budget in enumerate(budgets):
            self.budget_table.setItem(row, 0, QTableWidgetItem(str(budget['year'])))
            self.budget_table.setItem(row, 1, QTableWidgetItem(f"{budget['month']}月"))

            amount_item = QTableWidgetItem(f'¥ {budget["amount"]:,.2f}')
            amount_item.setForeground(Qt.GlobalColor.darkBlue)
            self.budget_table.setItem(row, 2, amount_item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            delete_btn = QPushButton('删除')
            delete_btn.setFixedSize(70, 36)
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
            delete_btn.clicked.connect(lambda checked, y=budget['year'], m=budget['month']: self.delete_budget(y, m))
            btn_layout.addWidget(delete_btn)

            self.budget_table.setCellWidget(row, 3, btn_widget)

    def load_categories(self):
        categories = self.db.get_all_categories('expense')
        self.category_combo.clear()
        for cat in categories:
            self.category_combo.addItem(cat['name'], cat['id'])

    def load_category_budgets(self, usage):
        category_budgets = usage['category_budgets']
        self.category_table.setRowCount(len(category_budgets))

        for row, cat in enumerate(category_budgets):
            self.category_table.setItem(row, 0, QTableWidgetItem(cat['category_name']))

            budget_item = QTableWidgetItem(f'¥ {cat["budget_amount"]:,.2f}')
            budget_item.setForeground(Qt.GlobalColor.darkBlue)
            self.category_table.setItem(row, 1, budget_item)

            spent_item = QTableWidgetItem(f'¥ {cat["spent_amount"]:,.2f}')
            spent_item.setForeground(Qt.GlobalColor.darkRed)
            self.category_table.setItem(row, 2, spent_item)

            remaining = cat['remaining']
            if remaining >= 0:
                remaining_item = QTableWidgetItem(f'¥ {remaining:,.2f}')
                remaining_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                remaining_item = QTableWidgetItem(f'-¥ {abs(remaining):,.2f}')
                remaining_item.setForeground(Qt.GlobalColor.darkRed)
            self.category_table.setItem(row, 3, remaining_item)

            progress_item = QTableWidgetItem()
            if cat['budget_amount'] > 0:
                progress = int(min(cat['percentage'], 100))
                progress_bar = QProgressBar()
                progress_bar.setValue(progress)
                progress_bar.setMinimumHeight(28)
                progress_bar.setMaximumHeight(32)
                if progress >= 100:
                    progress_bar.setStyleSheet("""
                        QProgressBar {
                            border: 1px solid #e0e0e0;
                            border-radius: 3px;
                            text-align: center;
                        }
                        QProgressBar::chunk {
                            background-color: #ea4335;
                            border-radius: 2px;
                        }
                    """)
                elif progress >= 80:
                    progress_bar.setStyleSheet("""
                        QProgressBar {
                            border: 1px solid #e0e0e0;
                            border-radius: 3px;
                            text-align: center;
                        }
                        QProgressBar::chunk {
                            background-color: #fbbc05;
                            border-radius: 2px;
                        }
                    """)
                else:
                    progress_bar.setStyleSheet("""
                        QProgressBar {
                            border: 1px solid #e0e0e0;
                            border-radius: 3px;
                            text-align: center;
                        }
                        QProgressBar::chunk {
                            background-color: #34a853;
                            border-radius: 2px;
                        }
                    """)
                self.category_table.setCellWidget(row, 4, progress_bar)
            else:
                progress_item.setText('-')
                self.category_table.setItem(row, 4, progress_item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            if cat['budget_amount'] > 0:
                delete_btn = QPushButton('删除')
                delete_btn.setFixedSize(70, 36)
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
                delete_btn.clicked.connect(lambda checked, cid=cat['category_id']: self.delete_category_budget(cid))
                btn_layout.addWidget(delete_btn)

            self.category_table.setCellWidget(row, 5, btn_widget)

    def set_monthly_budget(self):
        year = self.year_spin.value()
        month = self.month_combo.currentData()
        amount = self.budget_spin.value()

        if amount <= 0:
            QMessageBox.warning(self, '警告', '请输入有效的预算金额！')
            return

        if self.db.add_budget(year, month, amount):
            QMessageBox.information(self, '成功', f'{year}年{month}月预算设置成功！')
            self.refresh_data()
        else:
            QMessageBox.critical(self, '错误', '设置预算失败！')

    def delete_budget(self, year, month):
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除 {year}年{month}月 的预算吗？\n此操作将同时删除该月的所有分类子预算。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_budget(year, month):
                QMessageBox.information(self, '成功', '预算已删除！')
                self.refresh_data()
            else:
                QMessageBox.critical(self, '错误', '删除预算失败！')

    def set_category_budget(self):
        year = self.year_spin.value()
        month = self.month_combo.currentData()
        category_id = self.category_combo.currentData()
        amount = self.cat_budget_spin.value()

        if category_id is None:
            QMessageBox.warning(self, '警告', '请选择分类！')
            return

        if amount <= 0:
            QMessageBox.warning(self, '警告', '请输入有效的预算金额！')
            return

        budget = self.db.get_budget(year, month)
        if not budget:
            QMessageBox.warning(self, '警告', '请先设置月度总预算！')
            return

        if self.db.add_category_budget(budget['id'], category_id, amount):
            QMessageBox.information(self, '成功', f'{self.category_combo.currentText()} 分类预算设置成功！')
            self.refresh_data()
        else:
            QMessageBox.critical(self, '错误', '设置分类预算失败！')

    def delete_category_budget(self, category_id):
        year = self.year_spin.value()
        month = self.month_combo.currentData()
        budget = self.db.get_budget(year, month)

        if not budget:
            return

        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除该分类的预算吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            category_budgets = self.db.get_category_budgets(budget['id'])
            for cb in category_budgets:
                if cb['category_id'] == category_id:
                    if self.db.delete_category_budget(cb['id']):
                        QMessageBox.information(self, '成功', '分类预算已删除！')
                        self.refresh_data()
                    else:
                        QMessageBox.critical(self, '错误', '删除分类预算失败！')
                    break
