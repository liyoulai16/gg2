import sqlite3
import os
from datetime import datetime, timedelta
from calendar import monthrange


class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'accounting.db')
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                balance REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(name, type)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        self._migrate_transactions_table(cursor)

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                amount REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(year, month)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS category_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (budget_id) REFERENCES budgets (id),
                FOREIGN KEY (category_id) REFERENCES categories (id),
                UNIQUE(budget_id, category_id)
            )
        ''')

        self._create_default_categories(cursor)
        self._create_default_account(cursor)
        self._create_debt_tables(cursor)
        self._create_quick_entry_presets_table(cursor)
        self._create_recurring_tables(cursor)

        conn.commit()
        conn.close()

    def _create_debt_tables(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                counterparty TEXT NOT NULL,
                amount REAL NOT NULL,
                remaining_amount REAL NOT NULL,
                interest_rate REAL DEFAULT 0,
                start_date TEXT NOT NULL,
                due_date TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS debt_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                debt_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                due_date TEXT NOT NULL,
                paid_date TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (debt_id) REFERENCES debts (id)
            )
        ''')

    def _create_default_categories(self, cursor):
        default_categories = [
            ('工资', 'income'),
            ('奖金', 'income'),
            ('投资收益', 'income'),
            ('其他收入', 'income'),
            ('餐饮', 'expense'),
            ('交通', 'expense'),
            ('购物', 'expense'),
            ('娱乐', 'expense'),
            ('医疗', 'expense'),
            ('教育', 'expense'),
            ('住房', 'expense'),
            ('其他支出', 'expense'),
        ]

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for name, type_ in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, type, created_at)
                VALUES (?, ?, ?)
            ''', (name, type_, now))

    def _migrate_transactions_table(self, cursor):
        try:
            cursor.execute("PRAGMA table_info(transactions)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'is_deleted' not in columns:
                cursor.execute('ALTER TABLE transactions ADD COLUMN is_deleted INTEGER DEFAULT 0')
            if 'deleted_at' not in columns:
                cursor.execute('ALTER TABLE transactions ADD COLUMN deleted_at TEXT')
        except Exception as e:
            print(f"Error migrating transactions table: {e}")

    def _create_default_account(self, cursor):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT OR IGNORE INTO accounts (name, balance, created_at)
            VALUES (?, ?, ?)
        ''', ('现金', 0, now))

    def add_account(self, name, initial_balance=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO accounts (name, balance, created_at)
                VALUES (?, ?, ?)
            ''', (name, initial_balance, now))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_all_accounts(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, balance, created_at FROM accounts ORDER BY id')
        rows = cursor.fetchall()
        conn.close()
        return [{'id': row[0], 'name': row[1], 'balance': row[2], 'created_at': row[3]} for row in rows]

    def update_account(self, account_id, name=None, balance=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if name is not None:
                cursor.execute('UPDATE accounts SET name = ? WHERE id = ?', (name, account_id))
            if balance is not None:
                cursor.execute('UPDATE accounts SET balance = ? WHERE id = ?', (balance, account_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def delete_account(self, account_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE account_id = ?', (account_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return False
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        conn.commit()
        conn.close()
        return True

    def add_category(self, name, type_):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO categories (name, type, created_at)
                VALUES (?, ?, ?)
            ''', (name, type_, now))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_all_categories(self, type_=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        if type_:
            cursor.execute('SELECT id, name, type, created_at FROM categories WHERE type = ? ORDER BY id', (type_,))
        else:
            cursor.execute('SELECT id, name, type, created_at FROM categories ORDER BY id')
        rows = cursor.fetchall()
        conn.close()
        return [{'id': row[0], 'name': row[1], 'type': row[2], 'created_at': row[3]} for row in rows]

    def update_category(self, category_id, name=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if name is not None:
                cursor.execute('UPDATE categories SET name = ? WHERE id = ?', (name, category_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def delete_category(self, category_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE category_id = ?', (category_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return False
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()
        return True

    def add_transaction(self, account_id, category_id, type_, amount, description='', date=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO transactions (account_id, category_id, type, amount, description, date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, category_id, type_, amount, description, date, now))

            if type_ == 'income':
                cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, account_id))
            else:
                cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, account_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error adding transaction: {e}")
            return False
        finally:
            conn.close()

    def get_transactions(self, account_id=None, start_date=None, end_date=None, type_=None, include_deleted=False):
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT t.id, t.account_id, a.name as account_name, 
                   t.category_id, c.name as category_name,
                   t.type, t.amount, t.description, t.date, t.created_at,
                   t.is_deleted, t.deleted_at
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN categories c ON t.category_id = c.id
            WHERE 1=1
        '''
        params = []

        if not include_deleted:
            query += ' AND t.is_deleted = 0'

        if account_id:
            query += ' AND t.account_id = ?'
            params.append(account_id)
        if start_date:
            query += ' AND t.date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND t.date <= ?'
            params.append(end_date)
        if type_:
            query += ' AND t.type = ?'
            params.append(type_)

        query += ' ORDER BY t.date DESC, t.created_at DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            item = {
                'id': row[0],
                'account_id': row[1],
                'account_name': row[2],
                'category_id': row[3],
                'category_name': row[4],
                'type': row[5],
                'amount': row[6],
                'description': row[7],
                'date': row[8],
                'created_at': row[9]
            }
            if len(row) > 10:
                item['is_deleted'] = bool(row[10])
                item['deleted_at'] = row[11]
            result.append(item)
        return result

    def soft_delete_transaction(self, transaction_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT account_id, type, amount, is_deleted FROM transactions WHERE id = ?', (transaction_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False

            account_id, type_, amount, is_deleted = row
            if is_deleted:
                conn.close()
                return False

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('UPDATE transactions SET is_deleted = 1, deleted_at = ? WHERE id = ?', (now, transaction_id))

            if type_ == 'income':
                cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, account_id))
            else:
                cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, account_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error soft deleting transaction: {e}")
            return False
        finally:
            conn.close()

    def restore_transaction(self, transaction_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT account_id, type, amount, is_deleted FROM transactions WHERE id = ?', (transaction_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False

            account_id, type_, amount, is_deleted = row
            if not is_deleted:
                conn.close()
                return False

            cursor.execute('UPDATE transactions SET is_deleted = 0, deleted_at = NULL WHERE id = ?', (transaction_id,))

            if type_ == 'income':
                cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, account_id))
            else:
                cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, account_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error restoring transaction: {e}")
            return False
        finally:
            conn.close()

    def permanently_delete_transaction(self, transaction_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM transactions WHERE id = ? AND is_deleted = 1', (transaction_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            print(f"Error permanently deleting transaction: {e}")
            return False
        finally:
            conn.close()

    def get_deleted_transactions(self):
        return self.get_transactions(include_deleted=True)

    def delete_transaction(self, transaction_id):
        return self.soft_delete_transaction(transaction_id)

    def split_transaction(self, transaction_id, split_details):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT account_id, category_id, type, amount, description, date, is_deleted
                FROM transactions WHERE id = ?
            ''', (transaction_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "交易不存在"

            account_id, category_id, type_, original_amount, original_desc, date, is_deleted = row
            if is_deleted:
                conn.close()
                return False, "无法拆分已删除的交易"

            total_split_amount = sum(d['amount'] for d in split_details)
            if abs(total_split_amount - original_amount) > 0.01:
                conn.close()
                return False, f"拆分金额总和({total_split_amount})必须等于原交易金额({original_amount})"

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('UPDATE transactions SET is_deleted = 1, deleted_at = ? WHERE id = ?', (now, transaction_id))

            for detail in split_details:
                split_category_id = detail.get('category_id', category_id)
                split_amount = detail['amount']
                split_desc = detail.get('description', '')

                cursor.execute('''
                    INSERT INTO transactions (account_id, category_id, type, amount, description, date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (account_id, split_category_id, type_, split_amount, split_desc, date, now))

            conn.commit()
            return True, "拆分成功"
        except Exception as e:
            conn.rollback()
            print(f"Error splitting transaction: {e}")
            return False, str(e)
        finally:
            conn.close()

    def merge_transactions(self, transaction_ids, merge_category_id=None, merge_description=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if len(transaction_ids) < 2:
                conn.close()
                return False, "至少需要2条交易才能合并"

            placeholders = ','.join(['?'] * len(transaction_ids))
            cursor.execute(f'''
                SELECT id, account_id, category_id, type, amount, description, date, is_deleted
                FROM transactions WHERE id IN ({placeholders})
            ''', transaction_ids)
            rows = cursor.fetchall()

            if len(rows) != len(transaction_ids):
                conn.close()
                return False, "部分交易不存在"

            account_id = None
            type_ = None
            date = None
            total_amount = 0
            first_category_id = None

            for row in rows:
                t_id, t_account_id, t_category_id, t_type, t_amount, t_desc, t_date, t_is_deleted = row
                if t_is_deleted:
                    conn.close()
                    return False, "无法合并已删除的交易"

                if account_id is None:
                    account_id = t_account_id
                    type_ = t_type
                    date = t_date
                    first_category_id = t_category_id
                else:
                    if t_account_id != account_id:
                        conn.close()
                        return False, "只能合并同一账户的交易"
                    if t_type != type_:
                        conn.close()
                        return False, "只能合并相同类型的交易"

                total_amount += t_amount

            if merge_category_id is None:
                merge_category_id = first_category_id

            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute(f'''
                UPDATE transactions SET is_deleted = 1, deleted_at = ? WHERE id IN ({placeholders})
            ''', [now] + transaction_ids)

            cursor.execute('''
                INSERT INTO transactions (account_id, category_id, type, amount, description, date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (account_id, merge_category_id, type_, total_amount, merge_description, date, now))

            conn.commit()
            return True, "合并成功"
        except Exception as e:
            conn.rollback()
            print(f"Error merging transactions: {e}")
            return False, str(e)
        finally:
            conn.close()

    def get_transaction_by_id(self, transaction_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT t.id, t.account_id, a.name as account_name, 
                       t.category_id, c.name as category_name,
                       t.type, t.amount, t.description, t.date, t.created_at,
                       t.is_deleted, t.deleted_at
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                JOIN categories c ON t.category_id = c.id
                WHERE t.id = ?
            ''', (transaction_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'account_id': row[1],
                    'account_name': row[2],
                    'category_id': row[3],
                    'category_name': row[4],
                    'type': row[5],
                    'amount': row[6],
                    'description': row[7],
                    'date': row[8],
                    'created_at': row[9],
                    'is_deleted': bool(row[10]),
                    'deleted_at': row[11]
                }
            return None
        except Exception as e:
            print(f"Error getting transaction: {e}")
            return None
        finally:
            conn.close()

    def get_account_balance(self, account_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM accounts WHERE id = ?', (account_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    def get_total_balance(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(balance) FROM accounts')
        row = cursor.fetchone()
        conn.close()
        return row[0] if row and row[0] else 0

    def get_stats_by_period(self, start_date, end_date):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT type, SUM(amount) 
            FROM transactions 
            WHERE date >= ? AND date <= ? AND is_deleted = 0
            GROUP BY type
        ''', (start_date, end_date))
        rows = cursor.fetchall()
        conn.close()

        income = 0
        expense = 0
        for row in rows:
            if row[0] == 'income':
                income = row[1] or 0
            elif row[0] == 'expense':
                expense = row[1] or 0

        return {
            'income': income,
            'expense': expense,
            'balance': income - expense
        }

    def get_today_stats(self):
        today = datetime.now().strftime('%Y-%m-%d')
        return self.get_stats_by_period(today, today)

    def get_week_stats(self):
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return self.get_stats_by_period(
            start_of_week.strftime('%Y-%m-%d'),
            end_of_week.strftime('%Y-%m-%d')
        )

    def get_month_stats(self):
        today = datetime.now()
        _, days_in_month = monthrange(today.year, today.month)
        start_of_month = today.replace(day=1)
        end_of_month = today.replace(day=days_in_month)
        return self.get_stats_by_period(
            start_of_month.strftime('%Y-%m-%d'),
            end_of_month.strftime('%Y-%m-%d')
        )

    def get_year_stats(self):
        today = datetime.now()
        start_of_year = today.replace(month=1, day=1)
        end_of_year = today.replace(month=12, day=31)
        return self.get_stats_by_period(
            start_of_year.strftime('%Y-%m-%d'),
            end_of_year.strftime('%Y-%m-%d')
        )

    def get_category_stats(self, type_, start_date=None, end_date=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.type = ? AND t.is_deleted = 0
        '''
        params = [type_]

        if start_date:
            query += ' AND t.date >= ?'
            params.append(start_date)
        if end_date:
            query += ' AND t.date <= ?'
            params.append(end_date)

        query += ' GROUP BY c.id, c.name ORDER BY total DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        total = sum(row[1] or 0 for row in rows)
        result = []
        for row in rows:
            amount = row[1] or 0
            percentage = (amount / total * 100) if total > 0 else 0
            result.append({
                'name': row[0],
                'amount': amount,
                'percentage': percentage
            })

        return result, total

    def get_date_trend(self, start_date, end_date, type_=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        if type_:
            cursor.execute('''
                SELECT date, type, SUM(amount)
                FROM transactions
                WHERE date >= ? AND date <= ? AND type = ? AND is_deleted = 0
                GROUP BY date, type
                ORDER BY date
            ''', (start_date, end_date, type_))
        else:
            cursor.execute('''
                SELECT date, type, SUM(amount)
                FROM transactions
                WHERE date >= ? AND date <= ? AND is_deleted = 0
                GROUP BY date, type
                ORDER BY date
            ''', (start_date, end_date))

        rows = cursor.fetchall()
        conn.close()

        date_data = {}
        for row in rows:
            date = row[0]
            t_type = row[1]
            amount = row[2] or 0

            if date not in date_data:
                date_data[date] = {'income': 0, 'expense': 0}

            if t_type == 'income':
                date_data[date]['income'] = amount
            else:
                date_data[date]['expense'] = amount

        result = []
        for date in sorted(date_data.keys()):
            result.append({
                'date': date,
                'income': date_data[date]['income'],
                'expense': date_data[date]['expense'],
                'balance': date_data[date]['income'] - date_data[date]['expense']
            })

        return result

    def get_monthly_summary(self, year=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        if year is None:
            year = datetime.now().year

        cursor.execute('''
            SELECT 
                strftime('%Y-%m', date) as month,
                type,
                SUM(amount) as total
            FROM transactions
            WHERE strftime('%Y', date) = ? AND is_deleted = 0
            GROUP BY month, type
            ORDER BY month
        ''', (str(year),))

        rows = cursor.fetchall()
        conn.close()

        monthly_data = {}
        for row in rows:
            month = row[0]
            t_type = row[1]
            amount = row[2] or 0

            if month not in monthly_data:
                monthly_data[month] = {'income': 0, 'expense': 0}

            if t_type == 'income':
                monthly_data[month]['income'] = amount
            else:
                monthly_data[month]['expense'] = amount

        result = []
        for month in sorted(monthly_data.keys()):
            data = monthly_data[month]
            result.append({
                'month': month,
                'income': data['income'],
                'expense': data['expense'],
                'balance': data['income'] - data['expense']
            })

        return result

    def add_budget(self, year, month, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO budgets (year, month, amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(year, month) DO UPDATE SET amount = ?, updated_at = ?
            ''', (year, month, amount, now, now, amount, now))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error adding budget: {e}")
            return False
        finally:
            conn.close()

    def get_budget(self, year, month):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, year, month, amount, created_at, updated_at
            FROM budgets WHERE year = ? AND month = ?
        ''', (year, month))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'year': row[1],
                'month': row[2],
                'amount': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            }
        return None

    def get_all_budgets(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, year, month, amount, created_at, updated_at
            FROM budgets ORDER BY year DESC, month DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'year': row[1],
                'month': row[2],
                'amount': row[3],
                'created_at': row[4],
                'updated_at': row[5]
            })
        return result

    def delete_budget(self, year, month):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM category_budgets WHERE budget_id IN (SELECT id FROM budgets WHERE year = ? AND month = ?)', (year, month))
            cursor.execute('DELETE FROM budgets WHERE year = ? AND month = ?', (year, month))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting budget: {e}")
            return False
        finally:
            conn.close()

    def add_category_budget(self, budget_id, category_id, amount):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO category_budgets (budget_id, category_id, amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(budget_id, category_id) DO UPDATE SET amount = ?, updated_at = ?
            ''', (budget_id, category_id, amount, now, now, amount, now))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error adding category budget: {e}")
            return False
        finally:
            conn.close()

    def get_category_budgets(self, budget_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cb.id, cb.budget_id, cb.category_id, c.name as category_name,
                   cb.amount, cb.created_at, cb.updated_at
            FROM category_budgets cb
            JOIN categories c ON cb.category_id = c.id
            WHERE cb.budget_id = ?
        ''', (budget_id,))
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            result.append({
                'id': row[0],
                'budget_id': row[1],
                'category_id': row[2],
                'category_name': row[3],
                'amount': row[4],
                'created_at': row[5],
                'updated_at': row[6]
            })
        return result

    def delete_category_budget(self, category_budget_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM category_budgets WHERE id = ?', (category_budget_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting category budget: {e}")
            return False
        finally:
            conn.close()

    def get_budget_usage(self, year, month):
        conn = self.get_connection()
        cursor = conn.cursor()

        start_date = f"{year}-{month:02d}-01"
        end_date = f"{year}-{month:02d}-{monthrange(year, month)[1]}"

        cursor.execute('''
            SELECT COALESCE(SUM(amount), 0)
            FROM transactions
            WHERE type = 'expense' AND date >= ? AND date <= ? AND is_deleted = 0
        ''', (start_date, end_date))
        total_spent = cursor.fetchone()[0] or 0

        cursor.execute('''
            SELECT id, amount FROM budgets WHERE year = ? AND month = ?
        ''', (year, month))
        budget_row = cursor.fetchone()

        budget_id = None
        budget_amount = 0

        if budget_row:
            budget_id = budget_row[0]
            budget_amount = budget_row[1]

        category_budgets = []
        if budget_id:
            cursor.execute('''
                SELECT c.id, c.name, cb.amount as budget_amount,
                       COALESCE(SUM(t.amount), 0) as spent_amount
                FROM categories c
                LEFT JOIN category_budgets cb ON c.id = cb.category_id AND cb.budget_id = ?
                LEFT JOIN transactions t ON c.id = t.category_id AND t.type = 'expense' 
                    AND t.date >= ? AND t.date <= ? AND t.is_deleted = 0
                WHERE c.type = 'expense'
                GROUP BY c.id, c.name, cb.amount
            ''', (budget_id, start_date, end_date))

            rows = cursor.fetchall()
            for row in rows:
                budget_amt = row[2] or 0
                spent_amt = row[3] or 0
                category_budgets.append({
                    'category_id': row[0],
                    'category_name': row[1],
                    'budget_amount': budget_amt,
                    'spent_amount': spent_amt,
                    'remaining': budget_amt - spent_amt,
                    'percentage': (spent_amt / budget_amt * 100) if budget_amt > 0 else 0
                })

        conn.close()

        return {
            'year': year,
            'month': month,
            'budget_amount': budget_amount,
            'spent_amount': total_spent,
            'remaining': budget_amount - total_spent,
            'percentage': (total_spent / budget_amount * 100) if budget_amount > 0 else 0,
            'category_budgets': category_budgets
        }

    def check_over_budget(self, year, month):
        usage = self.get_budget_usage(year, month)
        alerts = []

        if usage['budget_amount'] > 0:
            if usage['spent_amount'] > usage['budget_amount']:
                alerts.append({
                    'type': 'total_over',
                    'message': f'本月总支出已超预算！预算: ¥{usage["budget_amount"]:,.2f}, 已支出: ¥{usage["spent_amount"]:,.2f}, 超支: ¥{usage["spent_amount"] - usage["budget_amount"]:,.2f}'
                })
            elif usage['percentage'] >= 80:
                alerts.append({
                    'type': 'total_warning',
                    'message': f'本月总支出已达预算的 {usage["percentage"]:.1f}%，请注意控制支出！'
                })

        for cat in usage['category_budgets']:
            if cat['budget_amount'] > 0:
                if cat['spent_amount'] > cat['budget_amount']:
                    alerts.append({
                        'type': 'category_over',
                        'category': cat['category_name'],
                        'message': f'{cat["category_name"]} 已超预算！预算: ¥{cat["budget_amount"]:,.2f}, 已支出: ¥{cat["spent_amount"]:,.2f}, 超支: ¥{cat["spent_amount"] - cat["budget_amount"]:,.2f}'
                    })
                elif cat['percentage'] >= 80:
                    alerts.append({
                        'type': 'category_warning',
                        'category': cat['category_name'],
                        'message': f'{cat["category_name"]} 支出已达预算的 {cat["percentage"]:.1f}%，请注意控制支出！'
                    })

        return alerts

    def add_debt(self, type_, counterparty, amount, interest_rate=0, start_date=None, due_date=None, description=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if start_date is None:
                start_date = datetime.now().strftime('%Y-%m-%d')
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO debts (type, counterparty, amount, remaining_amount, interest_rate, 
                                   start_date, due_date, status, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
            ''', (type_, counterparty, amount, amount, interest_rate, start_date, due_date, description, now, now))

            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            print(f"Error adding debt: {e}")
            return None
        finally:
            conn.close()

    def get_all_debts(self, type_=None, status=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT id, type, counterparty, amount, remaining_amount, interest_rate,
                   start_date, due_date, status, description, created_at, updated_at
            FROM debts WHERE 1=1
        '''
        params = []

        if type_:
            query += ' AND type = ?'
            params.append(type_)
        if status:
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row[0],
            'type': row[1],
            'counterparty': row[2],
            'amount': row[3],
            'remaining_amount': row[4],
            'interest_rate': row[5],
            'start_date': row[6],
            'due_date': row[7],
            'status': row[8],
            'description': row[9],
            'created_at': row[10],
            'updated_at': row[11]
        } for row in rows]

    def get_debt(self, debt_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, type, counterparty, amount, remaining_amount, interest_rate,
                   start_date, due_date, status, description, created_at, updated_at
            FROM debts WHERE id = ?
        ''', (debt_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'type': row[1],
                'counterparty': row[2],
                'amount': row[3],
                'remaining_amount': row[4],
                'interest_rate': row[5],
                'start_date': row[6],
                'due_date': row[7],
                'status': row[8],
                'description': row[9],
                'created_at': row[10],
                'updated_at': row[11]
            }
        return None

    def update_debt(self, debt_id, counterparty=None, amount=None, remaining_amount=None,
                    interest_rate=None, due_date=None, status=None, description=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updates = []
            params = []

            if counterparty is not None:
                updates.append('counterparty = ?')
                params.append(counterparty)
            if amount is not None:
                updates.append('amount = ?')
                params.append(amount)
            if remaining_amount is not None:
                updates.append('remaining_amount = ?')
                params.append(remaining_amount)
            if interest_rate is not None:
                updates.append('interest_rate = ?')
                params.append(interest_rate)
            if due_date is not None:
                updates.append('due_date = ?')
                params.append(due_date)
            if status is not None:
                updates.append('status = ?')
                params.append(status)
            if description is not None:
                updates.append('description = ?')
                params.append(description)

            if not updates:
                conn.close()
                return True

            updates.append('updated_at = ?')
            params.append(now)
            params.append(debt_id)

            query = f"UPDATE debts SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating debt: {e}")
            return False
        finally:
            conn.close()

    def delete_debt(self, debt_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM debt_payments WHERE debt_id = ?', (debt_id,))
            cursor.execute('DELETE FROM debts WHERE id = ?', (debt_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting debt: {e}")
            return False
        finally:
            conn.close()

    def add_debt_payment(self, debt_id, amount, due_date, description=''):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO debt_payments (debt_id, amount, due_date, status, description, created_at, updated_at)
                VALUES (?, ?, ?, 'pending', ?, ?, ?)
            ''', (debt_id, amount, due_date, description, now, now))

            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            print(f"Error adding debt payment: {e}")
            return None
        finally:
            conn.close()

    def get_debt_payments(self, debt_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, debt_id, amount, due_date, paid_date, status, description, created_at, updated_at
            FROM debt_payments WHERE debt_id = ? ORDER BY due_date
        ''', (debt_id,))
        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row[0],
            'debt_id': row[1],
            'amount': row[2],
            'due_date': row[3],
            'paid_date': row[4],
            'status': row[5],
            'description': row[6],
            'created_at': row[7],
            'updated_at': row[8]
        } for row in rows]

    def mark_payment_paid(self, payment_id, paid_date=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if paid_date is None:
                paid_date = datetime.now().strftime('%Y-%m-%d')
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('SELECT debt_id, amount FROM debt_payments WHERE id = ?', (payment_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False

            debt_id, payment_amount = row

            cursor.execute('''
                UPDATE debt_payments 
                SET status = 'paid', paid_date = ?, updated_at = ? 
                WHERE id = ?
            ''', (paid_date, now, payment_id))

            cursor.execute('''
                UPDATE debts 
                SET remaining_amount = remaining_amount - ?, updated_at = ? 
                WHERE id = ?
            ''', (payment_amount, now, debt_id))

            cursor.execute('SELECT remaining_amount FROM debts WHERE id = ?', (debt_id,))
            remaining = cursor.fetchone()[0]
            if remaining <= 0:
                cursor.execute('''
                    UPDATE debts SET status = 'completed', updated_at = ? WHERE id = ?
                ''', (now, debt_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error marking payment paid: {e}")
            return False
        finally:
            conn.close()

    def delete_debt_payment(self, payment_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT debt_id, amount, status FROM debt_payments WHERE id = ?', (payment_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False

            debt_id, payment_amount, status = row

            if status == 'paid':
                cursor.execute('''
                    UPDATE debts 
                    SET remaining_amount = remaining_amount + ?, status = 'active', updated_at = ? 
                    WHERE id = ?
                ''', (payment_amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), debt_id))

            cursor.execute('DELETE FROM debt_payments WHERE id = ?', (payment_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting debt payment: {e}")
            return False
        finally:
            conn.close()

    def get_debt_reminders(self, days_ahead=7):
        conn = self.get_connection()
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')
        reminder_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT d.id, d.type, d.counterparty, d.remaining_amount, d.due_date,
                   p.id as payment_id, p.amount as payment_amount, p.due_date as payment_due_date
            FROM debts d
            LEFT JOIN debt_payments p ON d.id = p.debt_id AND p.status = 'pending'
            WHERE d.status = 'active'
            ORDER BY d.id
        ''')

        rows = cursor.fetchall()
        conn.close()

        reminders = []
        today_dt = datetime.strptime(today, '%Y-%m-%d')

        for row in rows:
            debt_id, debt_type, counterparty, remaining, due_date, payment_id, payment_amount, payment_due_date = row

            due_dates_to_check = []
            if due_date:
                due_dates_to_check.append({
                    'type': 'debt',
                    'date': due_date,
                    'amount': remaining
                })
            if payment_due_date:
                due_dates_to_check.append({
                    'type': 'payment',
                    'date': payment_due_date,
                    'amount': payment_amount,
                    'payment_id': payment_id
                })

            for due in due_dates_to_check:
                try:
                    due_dt = datetime.strptime(due['date'], '%Y-%m-%d')
                    days_until_due = (due_dt - today_dt).days

                    if days_until_due < 0:
                        debt_type_label = '借出' if debt_type == 'lend' else '借入'
                        if due['type'] == 'debt':
                            message = f'🔴 【{debt_type_label}】{counterparty} 的债务已逾期 {abs(days_until_due)} 天！剩余金额: ¥{due["amount"]:,.2f}'
                        else:
                            message = f'🔴 【{debt_type_label}】{counterparty} 的还款计划已逾期 {abs(days_until_due)} 天！金额: ¥{due["amount"]:,.2f}'
                        reminders.append({
                            'debt_id': debt_id,
                            'type': debt_type,
                            'counterparty': counterparty,
                            'amount': due['amount'],
                            'due_date': due['date'],
                            'days_until_due': days_until_due,
                            'status': 'overdue',
                            'message': message
                        })
                    elif days_until_due <= days_ahead:
                        debt_type_label = '借出' if debt_type == 'lend' else '借入'
                        if due['type'] == 'debt':
                            if days_until_due == 0:
                                message = f'🟡 【{debt_type_label}】{counterparty} 的债务今天到期！剩余金额: ¥{due["amount"]:,.2f}'
                            else:
                                message = f'🟡 【{debt_type_label}】{counterparty} 的债务将在 {days_until_due} 天后到期！剩余金额: ¥{due["amount"]:,.2f}'
                        else:
                            if days_until_due == 0:
                                message = f'🟡 【{debt_type_label}】{counterparty} 的还款计划今天到期！金额: ¥{due["amount"]:,.2f}'
                            else:
                                message = f'🟡 【{debt_type_label}】{counterparty} 的还款计划将在 {days_until_due} 天后到期！金额: ¥{due["amount"]:,.2f}'
                        reminders.append({
                            'debt_id': debt_id,
                            'type': debt_type,
                            'counterparty': counterparty,
                            'amount': due['amount'],
                            'due_date': due['date'],
                            'days_until_due': days_until_due,
                            'status': 'upcoming',
                            'message': message
                        })
                except ValueError:
                    continue

        return reminders

    def get_debt_summary(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT type, status, SUM(remaining_amount) as total, COUNT(*) as count
            FROM debts GROUP BY type, status
        ''')
        rows = cursor.fetchall()
        conn.close()

        summary = {
            'lend_active': {'amount': 0, 'count': 0},
            'lend_completed': {'amount': 0, 'count': 0},
            'borrow_active': {'amount': 0, 'count': 0},
            'borrow_completed': {'amount': 0, 'count': 0}
        }

        for row in rows:
            type_, status, amount, count = row
            amount = amount or 0
            key = f"{type_}_{status}"
            if key in summary:
                summary[key] = {'amount': amount, 'count': count}

        return summary

    def _create_quick_entry_presets_table(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_entry_presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                description TEXT,
                is_default INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

    def add_quick_entry_preset(self, name, type_, account_id, category_id, description='', is_default=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if is_default:
                cursor.execute('UPDATE quick_entry_presets SET is_default = 0, updated_at = ? WHERE type = ?', (now, type_))
            
            cursor.execute('''
                INSERT INTO quick_entry_presets (name, type, account_id, category_id, description, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, type_, account_id, category_id, description, 1 if is_default else 0, now, now))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_all_quick_entry_presets(self, type_=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT p.id, p.name, p.type, p.account_id, a.name as account_name,
                   p.category_id, c.name as category_name, p.description, p.is_default
            FROM quick_entry_presets p
            JOIN accounts a ON p.account_id = a.id
            JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        '''
        params = []
        
        if type_:
            query += ' AND p.type = ?'
            params.append(type_)
        
        query += ' ORDER BY p.is_default DESC, p.id'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'account_id': row[3],
            'account_name': row[4],
            'category_id': row[5],
            'category_name': row[6],
            'description': row[7],
            'is_default': bool(row[8])
        } for row in rows]

    def get_default_quick_entry_preset(self, type_):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.id, p.name, p.type, p.account_id, a.name as account_name,
                   p.category_id, c.name as category_name, p.description, p.is_default
            FROM quick_entry_presets p
            JOIN accounts a ON p.account_id = a.id
            JOIN categories c ON p.category_id = c.id
            WHERE p.type = ? AND p.is_default = 1
            ORDER BY p.id
            LIMIT 1
        ''', (type_,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'account_id': row[3],
                'account_name': row[4],
                'category_id': row[5],
                'category_name': row[6],
                'description': row[7],
                'is_default': bool(row[8])
            }
        return None

    def update_quick_entry_preset(self, preset_id, name=None, account_id=None, category_id=None, description=None, is_default=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updates = []
            params = []
            
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            if account_id is not None:
                updates.append('account_id = ?')
                params.append(account_id)
            if category_id is not None:
                updates.append('category_id = ?')
                params.append(category_id)
            if description is not None:
                updates.append('description = ?')
                params.append(description)
            
            if is_default is not None:
                cursor.execute('SELECT type FROM quick_entry_presets WHERE id = ?', (preset_id,))
                row = cursor.fetchone()
                if row:
                    type_ = row[0]
                    cursor.execute('UPDATE quick_entry_presets SET is_default = 0, updated_at = ? WHERE type = ?', (now, type_))
                updates.append('is_default = ?')
                params.append(1 if is_default else 0)
            
            if not updates:
                conn.close()
                return True
            
            updates.append('updated_at = ?')
            params.append(now)
            params.append(preset_id)
            
            query = f"UPDATE quick_entry_presets SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating quick entry preset: {e}")
            return False
        finally:
            conn.close()

    def delete_quick_entry_preset(self, preset_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM quick_entry_presets WHERE id = ?', (preset_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting quick entry preset: {e}")
            return False
        finally:
            conn.close()

    def set_app_setting(self, key, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO app_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
            ''', (key, str(value), now, str(value), now))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error setting app setting: {e}")
            return False
        finally:
            conn.close()

    def get_app_setting(self, key, default_value=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row[0]
            return default_value
        except Exception as e:
            conn.close()
            print(f"Error getting app setting: {e}")
            return default_value

    def _create_recurring_tables(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                account_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                frequency TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                last_generated_date TEXT,
                is_active INTEGER DEFAULT 1,
                auto_generate INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recurring_generation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recurring_id INTEGER NOT NULL,
                transaction_id INTEGER,
                generated_date TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (recurring_id) REFERENCES recurring_transactions (id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')

    def add_recurring_transaction(self, name, type_, account_id, category_id, amount, 
                                   description='', frequency='monthly', start_date=None, 
                                   end_date=None, auto_generate=True):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if start_date is None:
                start_date = datetime.now().strftime('%Y-%m-%d')
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO recurring_transactions 
                (name, type, account_id, category_id, amount, description, 
                 frequency, start_date, end_date, is_active, auto_generate, 
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            ''', (name, type_, account_id, category_id, amount, description,
                  frequency, start_date, end_date, 1 if auto_generate else 0, now, now))

            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            print(f"Error adding recurring transaction: {e}")
            return None
        finally:
            conn.close()

    def get_all_recurring_transactions(self, active_only=True):
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT r.id, r.name, r.type, r.account_id, a.name as account_name,
                   r.category_id, c.name as category_name, r.amount, r.description,
                   r.frequency, r.start_date, r.end_date, r.last_generated_date,
                   r.is_active, r.auto_generate, r.created_at, r.updated_at
            FROM recurring_transactions r
            JOIN accounts a ON r.account_id = a.id
            JOIN categories c ON r.category_id = c.id
            WHERE 1=1
        '''
        params = []

        if active_only:
            query += ' AND r.is_active = 1'

        query += ' ORDER BY r.created_at DESC'

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [{
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'account_id': row[3],
            'account_name': row[4],
            'category_id': row[5],
            'category_name': row[6],
            'amount': row[7],
            'description': row[8],
            'frequency': row[9],
            'start_date': row[10],
            'end_date': row[11],
            'last_generated_date': row[12],
            'is_active': bool(row[13]),
            'auto_generate': bool(row[14]),
            'created_at': row[15],
            'updated_at': row[16]
        } for row in rows]

    def get_recurring_transaction(self, recurring_id):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT r.id, r.name, r.type, r.account_id, a.name as account_name,
                   r.category_id, c.name as category_name, r.amount, r.description,
                   r.frequency, r.start_date, r.end_date, r.last_generated_date,
                   r.is_active, r.auto_generate, r.created_at, r.updated_at
            FROM recurring_transactions r
            JOIN accounts a ON r.account_id = a.id
            JOIN categories c ON r.category_id = c.id
            WHERE r.id = ?
        ''', (recurring_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'account_id': row[3],
                'account_name': row[4],
                'category_id': row[5],
                'category_name': row[6],
                'amount': row[7],
                'description': row[8],
                'frequency': row[9],
                'start_date': row[10],
                'end_date': row[11],
                'last_generated_date': row[12],
                'is_active': bool(row[13]),
                'auto_generate': bool(row[14]),
                'created_at': row[15],
                'updated_at': row[16]
            }
        return None

    def update_recurring_transaction(self, recurring_id, name=None, type_=None, 
                                      account_id=None, category_id=None, amount=None,
                                      description=None, frequency=None, start_date=None,
                                      end_date=None, is_active=None, auto_generate=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updates = []
            params = []

            if name is not None:
                updates.append('name = ?')
                params.append(name)
            if type_ is not None:
                updates.append('type = ?')
                params.append(type_)
            if account_id is not None:
                updates.append('account_id = ?')
                params.append(account_id)
            if category_id is not None:
                updates.append('category_id = ?')
                params.append(category_id)
            if amount is not None:
                updates.append('amount = ?')
                params.append(amount)
            if description is not None:
                updates.append('description = ?')
                params.append(description)
            if frequency is not None:
                updates.append('frequency = ?')
                params.append(frequency)
            if start_date is not None:
                updates.append('start_date = ?')
                params.append(start_date)
            if end_date is not None:
                updates.append('end_date = ?')
                params.append(end_date)
            if is_active is not None:
                updates.append('is_active = ?')
                params.append(1 if is_active else 0)
            if auto_generate is not None:
                updates.append('auto_generate = ?')
                params.append(1 if auto_generate else 0)

            if not updates:
                conn.close()
                return True

            updates.append('updated_at = ?')
            params.append(now)
            params.append(recurring_id)

            query = f"UPDATE recurring_transactions SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating recurring transaction: {e}")
            return False
        finally:
            conn.close()

    def delete_recurring_transaction(self, recurring_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM recurring_generation_log WHERE recurring_id = ?', (recurring_id,))
            cursor.execute('DELETE FROM recurring_transactions WHERE id = ?', (recurring_id,))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting recurring transaction: {e}")
            return False
        finally:
            conn.close()

    def get_next_generation_date(self, start_date, frequency, last_date=None):
        try:
            current = datetime.strptime(start_date, '%Y-%m-%d')
            if last_date:
                current = datetime.strptime(last_date, '%Y-%m-%d')

            if frequency == 'daily':
                next_date = current + timedelta(days=1)
            elif frequency == 'weekly':
                next_date = current + timedelta(weeks=1)
            elif frequency == 'monthly':
                if current.month == 12:
                    next_month = 1
                    next_year = current.year + 1
                else:
                    next_month = current.month + 1
                    next_year = current.year
                _, days_in_month = monthrange(next_year, next_month)
                day = min(current.day, days_in_month)
                next_date = datetime(next_year, next_month, day)
            elif frequency == 'yearly':
                try:
                    next_date = current.replace(year=current.year + 1)
                except ValueError:
                    next_date = current.replace(year=current.year + 1, day=28)
            else:
                next_date = current

            return next_date.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Error calculating next generation date: {e}")
            return None

    def has_been_generated(self, recurring_id, date):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM recurring_generation_log 
            WHERE recurring_id = ? AND generated_date = ?
        ''', (recurring_id, date))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def log_generation(self, recurring_id, generated_date, status, transaction_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO recurring_generation_log 
                (recurring_id, transaction_id, generated_date, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (recurring_id, transaction_id, generated_date, status, now))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error logging generation: {e}")
            return False
        finally:
            conn.close()

    def generate_due_recurring_transactions(self):
        today = datetime.now().strftime('%Y-%m-%d')
        recurring_list = self.get_all_recurring_transactions(active_only=True)
        generated_transactions = []
        reminders = []

        for recurring in recurring_list:
            if not recurring['is_active']:
                continue

            start_date = recurring['start_date']
            end_date = recurring['end_date']
            last_generated = recurring['last_generated_date']
            frequency = recurring['frequency']
            auto_generate = recurring['auto_generate']

            if end_date and today > end_date:
                continue

            if today < start_date:
                continue

            current_date = start_date
            if last_generated:
                current_date = self.get_next_generation_date(start_date, frequency, last_generated)

            dates_to_generate = []
            while current_date and current_date <= today:
                if not self.has_been_generated(recurring['id'], current_date):
                    dates_to_generate.append(current_date)
                current_date = self.get_next_generation_date(start_date, frequency, current_date)

            for gen_date in dates_to_generate:
                if auto_generate:
                    success = self.add_transaction(
                        account_id=recurring['account_id'],
                        category_id=recurring['category_id'],
                        type_=recurring['type'],
                        amount=recurring['amount'],
                        description=recurring['description'] or '',
                        date=gen_date
                    )

                    if success:
                        self.log_generation(recurring['id'], gen_date, 'generated')
                        self.update_recurring_transaction(recurring['id'], last_generated_date=gen_date)
                        generated_transactions.append({
                            'recurring_name': recurring['name'],
                            'date': gen_date,
                            'amount': recurring['amount'],
                            'type': recurring['type']
                        })
                    else:
                        self.log_generation(recurring['id'], gen_date, 'failed')
                else:
                    self.log_generation(recurring['id'], gen_date, 'reminder')
                    reminders.append({
                        'recurring_name': recurring['name'],
                        'date': gen_date,
                        'amount': recurring['amount'],
                        'type': recurring['type'],
                        'account_name': recurring['account_name'],
                        'category_name': recurring['category_name']
                    })

        return {
            'generated': generated_transactions,
            'reminders': reminders
        }

    def get_recurring_reminders(self, days_ahead=7):
        today = datetime.now().strftime('%Y-%m-%d')
        today_dt = datetime.strptime(today, '%Y-%m-%d')
        reminder_date = (today_dt + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        recurring_list = self.get_all_recurring_transactions(active_only=True)
        reminders = []

        for recurring in recurring_list:
            if not recurring['is_active']:
                continue

            start_date = recurring['start_date']
            end_date = recurring['end_date']
            last_generated = recurring['last_generated_date']
            frequency = recurring['frequency']

            if end_date and start_date > end_date:
                continue

            current_date = start_date
            if last_generated:
                current_date = self.get_next_generation_date(start_date, frequency, last_generated)

            while current_date:
                if current_date > reminder_date:
                    break

                if today <= current_date <= reminder_date:
                    if not self.has_been_generated(recurring['id'], current_date):
                        days_until = (datetime.strptime(current_date, '%Y-%m-%d') - today_dt).days
                        type_label = '收入' if recurring['type'] == 'income' else '支出'
                        if days_until == 0:
                            message = f'【{type_label}】{recurring["name"]} 今天到期！金额: ¥{recurring["amount"]:,.2f}'
                        else:
                            message = f'【{type_label}】{recurring["name"]} 将在 {days_until} 天后到期！金额: ¥{recurring["amount"]:,.2f}'
                        
                        reminders.append({
                            'recurring_id': recurring['id'],
                            'name': recurring['name'],
                            'type': recurring['type'],
                            'amount': recurring['amount'],
                            'date': current_date,
                            'days_until': days_until,
                            'account_name': recurring['account_name'],
                            'category_name': recurring['category_name'],
                            'auto_generate': recurring['auto_generate'],
                            'message': message
                        })

                current_date = self.get_next_generation_date(start_date, frequency, current_date)

        return reminders
