from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QDateEdit, QSplitter, QFrame, QHeaderView,
    QAbstractItemView, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsLineItem,
    QGraphicsRectItem, QSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt, QDate, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from datetime import datetime, timedelta
from calendar import monthrange


class StatisticsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.chart_colors = [
            QColor('#4285f4'), QColor('#ea4335'), QColor('#34a853'),
            QColor('#fbbc05'), QColor('#9c27b0'), QColor('#00bcd4'),
            QColor('#ff9800'), QColor('#795548'), QColor('#607d8b'),
            QColor('#e91e63'), QColor('#009688'), QColor('#3f51b5')
        ]
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        overview_group = QGroupBox('📊 概览统计')
        overview_layout = QHBoxLayout(overview_group)
        overview_layout.setSpacing(20)

        self.today_card = self.create_stat_card('今日')
        overview_layout.addWidget(self.today_card)

        self.week_card = self.create_stat_card('本周')
        overview_layout.addWidget(self.week_card)

        self.month_card = self.create_stat_card('本月')
        overview_layout.addWidget(self.month_card)

        self.year_card = self.create_stat_card('全年')
        overview_layout.addWidget(self.year_card)

        layout.addWidget(overview_group)

        filter_group = QGroupBox('🔍 筛选条件')
        filter_layout = QHBoxLayout(filter_group)

        period_label = QLabel('时间范围:')
        self.period_combo = QComboBox()
        self.period_combo.addItems(['本周', '本月', '本年', '自定义'])
        self.period_combo.setFixedHeight(36)
        self.period_combo.currentIndexChanged.connect(self.on_period_changed)
        filter_layout.addWidget(period_label)
        filter_layout.addWidget(self.period_combo)

        start_label = QLabel('开始日期:')
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setFixedHeight(36)
        self.start_date_edit.setEnabled(False)
        filter_layout.addWidget(start_label)
        filter_layout.addWidget(self.start_date_edit)

        end_label = QLabel('结束日期:')
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setFixedHeight(36)
        self.end_date_edit.setEnabled(False)
        filter_layout.addWidget(end_label)
        filter_layout.addWidget(self.end_date_edit)

        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.setFixedHeight(36)
        refresh_btn.clicked.connect(self.refresh_data)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addWidget(filter_group)

        charts_splitter = QSplitter(Qt.Orientation.Horizontal)

        category_group = QGroupBox('📈 分类占比')
        category_layout = QVBoxLayout(category_group)

        category_type_layout = QHBoxLayout()
        self.category_type_combo = QComboBox()
        self.category_type_combo.addItems(['支出', '收入'])
        self.category_type_combo.setFixedHeight(36)
        self.category_type_combo.currentIndexChanged.connect(self.refresh_data)
        category_type_layout.addWidget(QLabel('类型:'))
        category_type_layout.addWidget(self.category_type_combo)
        category_type_layout.addStretch()
        category_layout.addLayout(category_type_layout)

        self.category_chart_view = PieChartView(self.chart_colors)
        self.category_chart_view.setMinimumHeight(300)
        category_layout.addWidget(self.category_chart_view)

        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(['分类', '金额', '占比'])
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.category_table.verticalHeader().setDefaultSectionSize(40)
        self.category_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.category_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setMaximumHeight(150)
        category_layout.addWidget(self.category_table)

        charts_splitter.addWidget(category_group)

        trend_group = QGroupBox('📉 日期趋势')
        trend_layout = QVBoxLayout(trend_group)

        trend_type_layout = QHBoxLayout()
        self.trend_type_combo = QComboBox()
        self.trend_type_combo.addItems(['收支对比', '仅收入', '仅支出'])
        self.trend_type_combo.setFixedHeight(36)
        self.trend_type_combo.currentIndexChanged.connect(self.refresh_data)
        trend_type_layout.addWidget(QLabel('显示:'))
        trend_type_layout.addWidget(self.trend_type_combo)
        trend_type_layout.addStretch()
        trend_layout.addLayout(trend_type_layout)

        self.trend_chart_view = LineChartView()
        self.trend_chart_view.setMinimumHeight(350)
        trend_layout.addWidget(self.trend_chart_view)

        charts_splitter.addWidget(trend_group)

        charts_splitter.setSizes([400, 500])
        layout.addWidget(charts_splitter)

        monthly_group = QGroupBox('📅 月度汇总')
        monthly_layout = QVBoxLayout(monthly_group)

        monthly_filter_layout = QHBoxLayout()
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2100)
        self.year_spin.setValue(datetime.now().year)
        self.year_spin.setFixedHeight(36)
        self.year_spin.valueChanged.connect(self.refresh_data)
        monthly_filter_layout.addWidget(QLabel('年份:'))
        monthly_filter_layout.addWidget(self.year_spin)
        monthly_filter_layout.addStretch()
        monthly_layout.addLayout(monthly_filter_layout)

        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(5)
        self.monthly_table.setHorizontalHeaderLabels(['月份', '收入', '支出', '结余', '净收益率'])
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monthly_table.verticalHeader().setDefaultSectionSize(50)
        self.monthly_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.monthly_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.monthly_table.setAlternatingRowColors(True)
        self.monthly_table.setMinimumHeight(200)
        monthly_layout.addWidget(self.monthly_table)

        layout.addWidget(monthly_group)
        
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll_area)

    def create_stat_card(self, title):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #5f6368;")
        layout.addWidget(title_label)

        income_label = QLabel('收入: ¥ 0.00')
        income_label.setStyleSheet("font-size: 13px; color: #34a853;")
        layout.addWidget(income_label)

        expense_label = QLabel('支出: ¥ 0.00')
        expense_label.setStyleSheet("font-size: 13px; color: #ea4335;")
        layout.addWidget(expense_label)

        balance_label = QLabel('结余: ¥ 0.00')
        balance_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(balance_label)

        card.income_label = income_label
        card.expense_label = expense_label
        card.balance_label = balance_label

        return card

    def on_period_changed(self, index):
        is_custom = self.period_combo.currentText() == '自定义'
        self.start_date_edit.setEnabled(is_custom)
        self.end_date_edit.setEnabled(is_custom)

    def get_date_range(self):
        period = self.period_combo.currentText()
        today = QDate.currentDate()

        if period == '本周':
            start = today.addDays(-today.dayOfWeek() + 1)
            end = start.addDays(6)
        elif period == '本月':
            start = QDate(today.year(), today.month(), 1)
            end = QDate(today.year(), today.month(), today.daysInMonth())
        elif period == '本年':
            start = QDate(today.year(), 1, 1)
            end = QDate(today.year(), 12, 31)
        else:
            start = self.start_date_edit.date()
            end = self.end_date_edit.date()

        return start.toString('yyyy-MM-dd'), end.toString('yyyy-MM-dd')

    def refresh_data(self):
        self.update_overview_stats()
        self.update_category_chart()
        self.update_trend_chart()
        self.update_monthly_summary()

    def update_overview_stats(self):
        today_stats = self.db.get_today_stats()
        week_stats = self.db.get_week_stats()
        month_stats = self.db.get_month_stats()
        year_stats = self.db.get_year_stats()

        self.update_stat_card(self.today_card, today_stats)
        self.update_stat_card(self.week_card, week_stats)
        self.update_stat_card(self.month_card, month_stats)
        self.update_stat_card(self.year_card, year_stats)

    def update_stat_card(self, card, stats):
        card.income_label.setText(f'收入: ¥ {stats["income"]:,.2f}')
        card.expense_label.setText(f'支出: ¥ {stats["expense"]:,.2f}')

        balance = stats['balance']
        if balance >= 0:
            card.balance_label.setText(f'结余: +¥ {balance:,.2f}')
            card.balance_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34a853;")
        else:
            card.balance_label.setText(f'结余: -¥ {abs(balance):,.2f}')
            card.balance_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ea4335;")

    def update_category_chart(self):
        type_text = self.category_type_combo.currentText()
        type_ = 'income' if type_text == '收入' else 'expense'
        start_date, end_date = self.get_date_range()

        categories, total = self.db.get_category_stats(type_, start_date, end_date)

        self.category_table.setRowCount(len(categories))
        for row, cat in enumerate(categories):
            self.category_table.setItem(row, 0, QTableWidgetItem(cat['name']))

            amount_item = QTableWidgetItem(f'¥ {cat["amount"]:,.2f}')
            if type_ == 'income':
                amount_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                amount_item.setForeground(Qt.GlobalColor.darkRed)
            self.category_table.setItem(row, 1, amount_item)

            self.category_table.setItem(row, 2, QTableWidgetItem(f'{cat["percentage"]:.1f}%'))

        if categories:
            self.category_chart_view.set_data(categories, type_)
        else:
            self.category_chart_view.set_data([], type_)

    def update_trend_chart(self):
        start_date, end_date = self.get_date_range()
        trend_type = self.trend_type_combo.currentText()

        type_ = None
        if trend_type == '仅收入':
            type_ = 'income'
        elif trend_type == '仅支出':
            type_ = 'expense'

        trend_data = self.db.get_date_trend(start_date, end_date, type_)

        self.trend_chart_view.set_data(trend_data, trend_type)

    def update_monthly_summary(self):
        year = self.year_spin.value()
        monthly_data = self.db.get_monthly_summary(year)

        self.monthly_table.setRowCount(len(monthly_data))

        for row, data in enumerate(monthly_data):
            self.monthly_table.setItem(row, 0, QTableWidgetItem(data['month']))

            income_item = QTableWidgetItem(f'¥ {data["income"]:,.2f}')
            income_item.setForeground(Qt.GlobalColor.darkGreen)
            self.monthly_table.setItem(row, 1, income_item)

            expense_item = QTableWidgetItem(f'¥ {data["expense"]:,.2f}')
            expense_item.setForeground(Qt.GlobalColor.darkRed)
            self.monthly_table.setItem(row, 2, expense_item)

            balance = data['balance']
            if balance >= 0:
                balance_item = QTableWidgetItem(f'+¥ {balance:,.2f}')
                balance_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                balance_item = QTableWidgetItem(f'-¥ {abs(balance):,.2f}')
                balance_item.setForeground(Qt.GlobalColor.darkRed)
            self.monthly_table.setItem(row, 3, balance_item)

            if data['income'] > 0:
                rate = (data['balance'] / data['income']) * 100
                rate_item = QTableWidgetItem(f'{rate:.1f}%')
            else:
                rate_item = QTableWidgetItem('-')
            self.monthly_table.setItem(row, 4, rate_item)


class PieChartView(QGraphicsView):
    def __init__(self, colors, parent=None):
        super().__init__(parent)
        self.colors = colors
        self.data = []
        self.type_ = 'expense'
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def set_data(self, data, type_):
        self.data = data
        self.type_ = type_
        self.draw_chart()

    def draw_chart(self):
        self.scene().clear()

        if not self.data:
            text = QGraphicsTextItem('暂无数据')
            text.setDefaultTextColor(QColor('#9e9e9e'))
            text.setFont(QFont('Microsoft YaHei', 14))
            text.setPos(self.width() / 2 - 40, self.height() / 2 - 10)
            self.scene().addItem(text)
            return

        view_rect = self.viewport().rect()
        center_x = view_rect.width() / 2
        center_y = view_rect.height() / 2
        radius = min(center_x, center_y) - 40

        total = sum(d['amount'] for d in self.data)

        start_angle = 0
        pie_items = []

        for i, item in enumerate(self.data):
            percentage = item['percentage']
            span_angle = (percentage / 100) * 360

            color = self.colors[i % len(self.colors)]

            pie_slice = PieSliceItem(center_x, center_y, radius, start_angle, span_angle, color)
            self.scene().addItem(pie_slice)
            pie_items.append((pie_slice, item))

            start_angle += span_angle

        legend_x = 20
        legend_y = 10
        legend_height = 20

        for i, item in enumerate(self.data[:6]):
            color = self.colors[i % len(self.colors)]

            color_rect = QGraphicsRectItem(legend_x, legend_y + i * (legend_height + 5), 15, 15)
            color_rect.setBrush(QBrush(color))
            color_rect.setPen(QPen(Qt.GlobalColor.transparent))
            self.scene().addItem(color_rect)

            legend_text = QGraphicsTextItem(f"{item['name']} ({item['percentage']:.1f}%)")
            legend_text.setDefaultTextColor(QColor('#5f6368'))
            legend_text.setFont(QFont('Microsoft YaHei', 9))
            legend_text.setPos(legend_x + 20, legend_y + i * (legend_height + 5) - 2)
            self.scene().addItem(legend_text)


class PieSliceItem(QGraphicsEllipseItem):
    def __init__(self, cx, cy, radius, start_angle, span_angle, color, parent=None):
        super().__init__(parent)
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.start_angle = start_angle
        self.span_angle = span_angle
        self.color = color

        self.setRect(cx - radius, cy - radius, radius * 2, radius * 2)
        self.setBrush(QBrush(color))
        self.setPen(QPen(Qt.GlobalColor.white, 2))
        self.setStartAngle(int(start_angle * 16))
        self.setSpanAngle(int(span_angle * 16))


class LineChartView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.trend_type = '收支对比'
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def set_data(self, data, trend_type):
        self.data = data
        self.trend_type = trend_type
        self.draw_chart()

    def draw_chart(self):
        self.scene().clear()

        if not self.data:
            text = QGraphicsTextItem('暂无数据')
            text.setDefaultTextColor(QColor('#9e9e9e'))
            text.setFont(QFont('Microsoft YaHei', 14))
            text.setPos(self.width() / 2 - 40, self.height() / 2 - 10)
            self.scene().addItem(text)
            return

        view_rect = self.viewport().rect()
        padding = 60
        chart_width = view_rect.width() - padding * 2
        chart_height = view_rect.height() - padding * 2

        if chart_width <= 0 or chart_height <= 0:
            return

        max_value = 0
        if self.trend_type == '仅收入':
            max_value = max(d['income'] for d in self.data) if self.data else 0
        elif self.trend_type == '仅支出':
            max_value = max(d['expense'] for d in self.data) if self.data else 0
        else:
            max_income = max(d['income'] for d in self.data) if self.data else 0
            max_expense = max(d['expense'] for d in self.data) if self.data else 0
            max_value = max(max_income, max_expense)

        if max_value == 0:
            max_value = 1

        grid_lines = 5
        for i in range(grid_lines + 1):
            y = padding + (chart_height / grid_lines) * i
            value = max_value * (1 - i / grid_lines)

            line = QGraphicsLineItem(padding, y, padding + chart_width, y)
            line.setPen(QPen(QColor('#e0e0e0'), 1, Qt.PenStyle.DashLine))
            self.scene().addItem(line)

            label = QGraphicsTextItem(f'¥ {value:,.0f}')
            label.setDefaultTextColor(QColor('#9e9e9e'))
            label.setFont(QFont('Microsoft YaHei', 9))
            label.setTextWidth(50)
            label.setPos(5, y - 10)
            self.scene().addItem(label)

        if self.trend_type == '收支对比':
            income_color = QColor('#34a853')
            expense_color = QColor('#ea4335')
            self.draw_line(padding, padding, chart_width, chart_height,
                           [d['income'] for d in self.data], max_value, income_color)
            self.draw_line(padding, padding, chart_width, chart_height,
                           [d['expense'] for d in self.data], max_value, expense_color)

            legend_income = QGraphicsRectItem(padding, 10, 15, 15)
            legend_income.setBrush(QBrush(income_color))
            legend_income.setPen(QPen(Qt.GlobalColor.transparent))
            self.scene().addItem(legend_income)

            legend_income_text = QGraphicsTextItem('收入')
            legend_income_text.setDefaultTextColor(QColor('#5f6368'))
            legend_income_text.setFont(QFont('Microsoft YaHei', 10))
            legend_income_text.setPos(padding + 20, 8)
            self.scene().addItem(legend_income_text)

            legend_expense = QGraphicsRectItem(padding + 80, 10, 15, 15)
            legend_expense.setBrush(QBrush(expense_color))
            legend_expense.setPen(QPen(Qt.GlobalColor.transparent))
            self.scene().addItem(legend_expense)

            legend_expense_text = QGraphicsTextItem('支出')
            legend_expense_text.setDefaultTextColor(QColor('#5f6368'))
            legend_expense_text.setFont(QFont('Microsoft YaHei', 10))
            legend_expense_text.setPos(padding + 100, 8)
            self.scene().addItem(legend_expense_text)

        elif self.trend_type == '仅收入':
            income_color = QColor('#34a853')
            self.draw_line(padding, padding, chart_width, chart_height,
                           [d['income'] for d in self.data], max_value, income_color)

        else:
            expense_color = QColor('#ea4335')
            self.draw_line(padding, padding, chart_width, chart_height,
                           [d['expense'] for d in self.data], max_value, expense_color)

        step = max(1, len(self.data) // 7)
        for i in range(0, len(self.data), step):
            x = padding + (chart_width / max(len(self.data) - 1, 1)) * i
            date_label = self.data[i]['date'][5:]

            label = QGraphicsTextItem(date_label)
            label.setDefaultTextColor(QColor('#9e9e9e'))
            label.setFont(QFont('Microsoft YaHei', 9))
            label.setPos(x - 15, padding + chart_height + 5)
            self.scene().addItem(label)

    def draw_line(self, x0, y0, width, height, values, max_value, color):
        if len(values) < 2:
            return

        points = []
        for i, value in enumerate(values):
            x = x0 + (width / max(len(values) - 1, 1)) * i
            y = y0 + height - (value / max_value) * height
            points.append((x, y))

        path = QPainterPath()
        path.moveTo(points[0][0], points[0][1])
        for x, y in points[1:]:
            path.lineTo(x, y)

        pen = QPen(color, 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)

        path_item = self.scene().addPath(path, pen)

        for x, y in points:
            point_item = QGraphicsEllipseItem(x - 4, y - 4, 8, 8)
            point_item.setBrush(QBrush(color))
            point_item.setPen(QPen(Qt.GlobalColor.white, 1))
            self.scene().addItem(point_item)
