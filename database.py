import sqlite3
import os
from datetime import datetime


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

        self._create_default_categories(cursor)
        self._create_default_account(cursor)

        conn.commit()
        conn.close()

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
