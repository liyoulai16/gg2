from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QCheckBox, QComboBox, QDateEdit, QRadioButton,
    QButtonGroup, QFileDialog, QMessageBox, QProgressBar,
    QTextEdit, QWidget, QSpinBox, QFrame
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime
import os


class ExportDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle('导出数据')
        self.setMinimumSize(500, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel('📤 数据导出')
        title_label.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        format_group = QGroupBox('导出格式')
        format_layout = QVBoxLayout(format_group)

        self.format_group = QButtonGroup(self)
        self.csv_radio = QRadioButton('CSV 格式（通用，推荐）')
        self.excel_radio = QRadioButton('Excel 格式（带格式化）')
        self.csv_radio.setChecked(True)

        self.format_group.addButton(self.csv_radio)
        self.format_group.addButton(self.excel_radio)

        format_layout.addWidget(self.csv_radio)
        format_layout.addWidget(self.excel_radio)
        layout.addWidget(format_group)

        scope_group = QGroupBox('导出范围')
        scope_layout = QVBoxLayout(scope_group)

        self.scope_group = QButtonGroup(self)
        self.all_radio = QRadioButton('全部交易记录')
        self.date_range_radio = QRadioButton('指定日期范围')
        self.all_radio.setChecked(True)

        self.scope_group.addButton(self.all_radio)
        self.scope_group.addButton(self.date_range_radio)

        scope_layout.addWidget(self.all_radio)
        scope_layout.addWidget(self.date_range_radio)

        date_frame = QFrame()
        date_layout = QHBoxLayout(date_frame)
        date_layout.setContentsMargins(20, 0, 0, 0)

        date_layout.addWidget(QLabel('开始日期:'))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel('结束日期:'))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_layout.addWidget(self.end_date)

        scope_layout.addWidget(date_frame)

        self.date_range_radio.toggled.connect(lambda checked: date_frame.setEnabled(checked))
        date_frame.setEnabled(False)

        layout.addWidget(scope_group)

        filter_group = QGroupBox('筛选条件')
        filter_layout = QVBoxLayout(filter_group)

        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel('账户:'))
        self.account_combo = QComboBox()
        self.account_combo.addItem('全部账户', None)
        for account in self.db.get_all_accounts():
            self.account_combo.addItem(account['name'], account['id'])
        account_layout.addWidget(self.account_combo)
        account_layout.addStretch()
        filter_layout.addLayout(account_layout)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel('类型:'))
        self.type_combo = QComboBox()
        self.type_combo.addItem('全部类型', None)
        self.type_combo.addItem('仅收入', 'income')
        self.type_combo.addItem('仅支出', 'expense')
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        filter_layout.addLayout(type_layout)

        layout.addWidget(filter_group)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.export_btn = QPushButton('导出数据')
        self.export_btn.setMinimumWidth(120)
        self.export_btn.setStyleSheet("""
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
        self.export_btn.clicked.connect(self.do_export)
        button_layout.addWidget(self.export_btn)

        layout.addLayout(button_layout)

    def get_export_params(self):
        params = {}
        params['format'] = 'csv' if self.csv_radio.isChecked() else 'excel'
        
        if self.date_range_radio.isChecked():
            params['start_date'] = self.start_date.date().toString('yyyy-MM-dd')
            params['end_date'] = self.end_date.date().toString('yyyy-MM-dd')
        else:
            params['start_date'] = None
            params['end_date'] = None

        params['account_id'] = self.account_combo.currentData()
        params['type_'] = self.type_combo.currentData()

        return params

    def do_export(self):
        from import_export import ImportExportManager, HAS_OPENPYXL

        params = self.get_export_params()
        manager = ImportExportManager(self.db)

        if params['format'] == 'excel' and not HAS_OPENPYXL:
            QMessageBox.warning(
                self, '警告',
                '未安装 openpyxl 库，无法导出 Excel。\n'
                '请运行: pip install openpyxl\n\n'
                '将使用 CSV 格式导出。'
            )
            params['format'] = 'csv'

        default_filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ext = '.csv' if params['format'] == 'csv' else '.xlsx'
        filter_str = "CSV 文件 (*.csv)" if params['format'] == 'csv' else "Excel 文件 (*.xlsx)"

        filepath, _ = QFileDialog.getSaveFileName(
            self, '保存文件', default_filename + ext, filter_str
        )

        if not filepath:
            return

        if params['format'] == 'csv':
            success, message = manager.export_transactions_to_csv(
                filepath,
                start_date=params['start_date'],
                end_date=params['end_date'],
                account_id=params['account_id'],
                type_=params['type_']
            )
        else:
            success, message = manager.export_transactions_to_excel(
                filepath,
                start_date=params['start_date'],
                end_date=params['end_date'],
                account_id=params['account_id'],
                type_=params['type_']
            )

        if success:
            QMessageBox.information(self, '成功', message)
            self.accept()
        else:
            QMessageBox.warning(self, '失败', message)


class ImportDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.filepath = None
        self.setWindowTitle('导入数据')
        self.setMinimumSize(600, 500)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel('📥 数据导入')
        title_label.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        file_group = QGroupBox('选择文件')
        file_layout = QHBoxLayout(file_group)

        self.file_label = QLabel('未选择文件')
        self.file_label.setStyleSheet("color: #666;")
        file_layout.addWidget(self.file_label)

        self.browse_btn = QPushButton('浏览...')
        self.browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_btn)

        layout.addWidget(file_group)

        options_group = QGroupBox('导入选项')
        options_layout = QVBoxLayout(options_group)

        self.create_missing_check = QCheckBox('自动创建不存在的账户和分类')
        self.create_missing_check.setChecked(True)
        options_layout.addWidget(self.create_missing_check)

        format_label = QLabel('CSV 文件格式说明：')
        format_label.setStyleSheet("font-weight: bold; color: #5f6368;")
        options_layout.addWidget(format_label)

        format_info = QTextEdit()
        format_info.setReadOnly(True)
        format_info.setMaximumHeight(120)
        format_info.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        format_info.setText(
            "必需列: 日期, 类型, 账户, 分类, 金额\n"
            "可选列: 描述\n\n"
            "类型取值: 收入/income 或 支出/expense\n"
            "日期格式: YYYY-MM-DD (如: 2024-01-15)"
        )
        options_layout.addWidget(format_info)

        layout.addWidget(options_group)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.import_btn = QPushButton('开始导入')
        self.import_btn.setMinimumWidth(120)
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
        """)
        self.import_btn.clicked.connect(self.do_import)
        button_layout.addWidget(self.import_btn)

        layout.addLayout(button_layout)

    def browse_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, '选择 CSV 文件', '', 'CSV 文件 (*.csv)'
        )
        if filepath:
            self.filepath = filepath
            self.file_label.setText(os.path.basename(filepath))
            self.file_label.setStyleSheet("color: #34a853; font-weight: bold;")
            self.import_btn.setEnabled(True)

    def do_import(self):
        if not self.filepath:
            return

        from import_export import ImportExportManager

        reply = QMessageBox.question(
            self, '确认导入',
            '导入的数据将添加到现有数据中。\n'
            '建议在导入前先备份数据库。\n\n'
            '确定要继续吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        manager = ImportExportManager(self.db)
        create_missing = self.create_missing_check.isChecked()

        success, message, errors = manager.import_transactions_from_csv(
            self.filepath,
            create_missing=create_missing
        )

        if errors:
            error_msg = '\n'.join(errors[:10])
            if len(errors) > 10:
                error_msg += f'\n... 还有 {len(errors) - 10} 个错误'
            
            QMessageBox.warning(
                self, '导入完成',
                f'{message}\n\n错误详情:\n{error_msg}'
            )
        else:
            QMessageBox.information(self, '成功', message)

        self.accept()


class BackupRestoreDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle('数据备份与恢复')
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title_label = QLabel('💾 数据备份与恢复')
        title_label.setFont(QFont('Microsoft YaHei', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        backup_group = QGroupBox('备份数据')
        backup_layout = QVBoxLayout(backup_group)

        backup_desc = QLabel(
            '创建完整数据库备份，包含所有账户、分类、交易记录、预算、债务等数据。\n'
            '备份文件可以用于恢复到任何时间点的数据状态。'
        )
        backup_desc.setWordWrap(True)
        backup_desc.setStyleSheet("color: #5f6368;")
        backup_layout.addWidget(backup_desc)

        backup_btn_layout = QHBoxLayout()
        backup_btn_layout.addStretch()

        self.backup_btn = QPushButton('📦 创建备份')
        self.backup_btn.setMinimumWidth(150)
        self.backup_btn.setMinimumHeight(45)
        self.backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
        """)
        self.backup_btn.clicked.connect(self.do_backup)
        backup_btn_layout.addWidget(self.backup_btn)

        backup_layout.addLayout(backup_btn_layout)
        layout.addWidget(backup_group)

        restore_group = QGroupBox('恢复数据')
        restore_layout = QVBoxLayout(restore_group)

        restore_desc = QLabel(
            '从之前的备份文件恢复数据。\n'
            '⚠️ 警告：恢复将覆盖当前所有数据，请确保已备份最新数据！'
        )
        restore_desc.setWordWrap(True)
        restore_desc.setStyleSheet("color: #ea4335;")
        restore_layout.addWidget(restore_desc)

        restore_btn_layout = QHBoxLayout()
        restore_btn_layout.addStretch()

        self.restore_btn = QPushButton('🔄 从备份恢复')
        self.restore_btn.setMinimumWidth(150)
        self.restore_btn.setMinimumHeight(45)
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #ea4335;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d33427;
            }
        """)
        self.restore_btn.clicked.connect(self.do_restore)
        restore_btn_layout.addWidget(self.restore_btn)

        restore_layout.addLayout(restore_btn_layout)
        layout.addWidget(restore_group)

        layout.addStretch()

        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()

        self.close_btn = QPushButton('关闭')
        self.close_btn.setMinimumWidth(100)
        self.close_btn.clicked.connect(self.accept)
        close_btn_layout.addWidget(self.close_btn)

        layout.addLayout(close_btn_layout)

    def do_backup(self):
        from import_export import ImportExportManager

        default_dir = os.path.join(os.path.expanduser('~'), 'Documents', 'AccountingBackups')
        os.makedirs(default_dir, exist_ok=True)

        filepath = QFileDialog.getExistingDirectory(
            self, '选择备份保存位置', default_dir
        )

        if not filepath:
            return

        manager = ImportExportManager(self.db)
        success, message = manager.backup_database(filepath)

        if success:
            QMessageBox.information(self, '备份成功', message)
        else:
            QMessageBox.warning(self, '备份失败', message)

    def do_restore(self):
        reply = QMessageBox.warning(
            self, '警告',
            '恢复数据将覆盖当前所有数据！\n\n'
            '此操作不可撤销，建议先创建当前数据的备份。\n\n'
            '确定要继续吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        filepath, _ = QFileDialog.getOpenFileName(
            self, '选择备份文件', '', '数据库备份 (*.db)'
        )

        if not filepath:
            return

        from import_export import ImportExportManager
        manager = ImportExportManager(self.db)
        success, message = manager.restore_database(filepath)

        if success:
            QMessageBox.information(self, '恢复成功', message + '\n\n应用将退出以完成恢复。')
            self.accept()
        else:
            QMessageBox.warning(self, '恢复失败', message)
