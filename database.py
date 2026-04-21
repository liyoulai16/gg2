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
                FOREIGN KEY (account_id) REFERENCES accounts (id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        ''')

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

    def get_transactions(self, account_id=None, start_date=None, end_date=None, type_=None):
        conn = self.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT t.id, t.account_id, a.name as account_name, 
                   t.category_id, c.name as category_name,
                   t.type, t.amount, t.description, t.date, t.created_at
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN categories c ON t.category_id = c.id
            WHERE 1=1
        '''
        params = []

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

        return [{
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
        } for row in rows]

    def delete_transaction(self, transaction_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT account_id, type, amount FROM transactions WHERE id = ?', (transaction_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False

            account_id, type_, amount = row

            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))

            if type_ == 'income':
                cursor.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, account_id))
            else:
                cursor.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, account_id))

            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error deleting transaction: {e}")
            return False
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
            WHERE date >= ? AND date <= ?
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
            WHERE t.type = ?
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
                WHERE date >= ? AND date <= ? AND type = ?
                GROUP BY date, type
                ORDER BY date
            ''', (start_date, end_date, type_))
        else:
            cursor.execute('''
                SELECT date, type, SUM(amount)
                FROM transactions
                WHERE date >= ? AND date <= ?
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
            WHERE strftime('%Y', date) = ?
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
            WHERE type = 'expense' AND date >= ? AND date <= ?
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
                    AND t.date >= ? AND t.date <= ?
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
