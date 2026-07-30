# database.py – DEVILS WILL RISE EDITION 🔥
import sqlite3
import json
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DATABASE_URL", "bot.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        total_orders INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0,
        created_at TEXT
    )''')
    
    # Accounts table
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        _id TEXT PRIMARY KEY,
        country_flag TEXT,
        country TEXT,
        number TEXT,
        password TEXT,
        email TEXT,
        price REAL,
        status TEXT DEFAULT 'available',
        sold_to INTEGER DEFAULT NULL,
        sold_at TEXT DEFAULT NULL
    )''')
    
    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        _id TEXT PRIMARY KEY,
        user_id INTEGER,
        username TEXT,
        full_name TEXT,
        account_id TEXT,
        amount REAL,
        exact_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'pending',
        screenshot TEXT DEFAULT NULL,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (account_id) REFERENCES accounts(_id)
    )''')
    
    # Sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        _id TEXT PRIMARY KEY,
        order_id TEXT,
        user_id INTEGER,
        account_id TEXT,
        created_at TEXT,
        expires_at TEXT
    )''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")


# ═══════════════════════════════════════════════════════════════════
# 🔥 USER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def create_user(user_id, username, full_name):
    """Create new user if not exists"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (user_id, username, full_name, created_at)
                 VALUES (?, ?, ?, ?)''', (user_id, username, full_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logger.info(f"✅ User created: {user_id}")

async def get_user(user_id):
    """Get user by ID"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "total_orders": row[3],
            "total_spent": row[4],
            "created_at": row[5]
        }
    return None

async def update_user_stats(user_id, amount):
    """Update user total orders and spent"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('''UPDATE users 
                 SET total_orders = total_orders + 1,
                     total_spent = total_spent + ?
                 WHERE user_id = ?''', (amount, user_id))
    conn.commit()
    conn.close()
    logger.info(f"✅ User stats updated: {user_id} +₹{amount}")


# ═══════════════════════════════════════════════════════════════════
# 🔥 ACCOUNT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def add_account(country_flag, country, number, password, price, email=""):
    """Add new account to database"""
    import uuid
    _id = f"acc_{uuid.uuid4().hex[:8]}"
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO accounts (_id, country_flag, country, number, password, email, price)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', (_id, country_flag, country, number, password, email, price))
    conn.commit()
    conn.close()
    logger.info(f"✅ Account added: {_id}")
    return _id

async def get_account(account_id):
    """Get account by ID"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM accounts WHERE _id = ?', (account_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "_id": row[0],
            "country_flag": row[1],
            "country": row[2],
            "number": row[3],
            "password": row[4],
            "email": row[5],
            "price": row[6],
            "status": row[7],
            "sold_to": row[8],
            "sold_at": row[9]
        }
    return None

async def get_available_accounts():
    """Get all available accounts"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM accounts WHERE status = "available"')
    rows = c.fetchall()
    conn.close()
    accounts = []
    for row in rows:
        accounts.append({
            "_id": row[0],
            "country_flag": row[1],
            "country": row[2],
            "number": row[3],
            "password": row[4],
            "email": row[5],
            "price": row[6],
            "status": row[7]
        })
    return accounts

async def get_all_accounts():
    """Get all accounts (for stats)"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT _id, status FROM accounts')
    rows = c.fetchall()
    conn.close()
    return [{"_id": r[0], "status": r[1]} for r in rows]

async def mark_account_sold(account_id, user_id):
    """Mark account as sold"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('''UPDATE accounts 
                 SET status = "sold", sold_to = ?, sold_at = ?
                 WHERE _id = ?''', (user_id, datetime.now().isoformat(), account_id))
    conn.commit()
    conn.close()
    logger.info(f"✅ Account sold: {account_id} → user {user_id}")


# ═══════════════════════════════════════════════════════════════════
# 🔥 ORDER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def create_order(user_id, username, full_name, account_id, amount):
    """Create new order"""
    import uuid
    _id = f"ord_{uuid.uuid4().hex[:8]}"
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO orders (_id, user_id, username, full_name, account_id, amount, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', (_id, user_id, username, full_name, account_id, amount, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    logger.info(f"✅ Order created: {_id}")
    return _id

async def get_order(order_id):
    """Get order by ID"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE _id = ?', (order_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "_id": row[0],
            "user_id": row[1],
            "username": row[2],
            "full_name": row[3],
            "account_id": row[4],
            "amount": row[5],
            "exact_amount": row[6],
            "status": row[7],
            "screenshot": row[8],
            "created_at": row[9]
        }
    return None

async def get_user_orders(user_id):
    """Get all orders for a user"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    rows = c.fetchall()
    conn.close()
    orders = []
    for row in rows:
        orders.append({
            "_id": row[0],
            "amount": row[5],
            "status": row[7],
            "created_at": row[9]
        })
    return orders

async def get_pending_orders():
    """Get all pending orders"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE status = "pending" ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    orders = []
    for row in rows:
        orders.append({
            "_id": row[0],
            "user_id": row[1],
            "username": row[2],
            "full_name": row[3],
            "account_id": row[4],
            "amount": row[5],
            "exact_amount": row[6],
            "status": row[7],
            "screenshot": row[8],
            "created_at": row[9]
        })
    return orders

async def set_order_exact_amount(order_id, exact_amount):
    """Set exact amount for order (after QR generation)"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE orders SET exact_amount = ? WHERE _id = ?', (exact_amount, order_id))
    conn.commit()
    conn.close()
    logger.info(f"✅ Exact amount set: {order_id} → ₹{exact_amount}")

async def set_order_screenshot(order_id, file_id):
    """Save screenshot file_id to order"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE orders SET screenshot = ? WHERE _id = ?', (file_id, order_id))
    conn.commit()
    conn.close()
    logger.info(f"✅ Screenshot saved: {order_id}")

async def approve_order(order_id):
    """Approve order"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = "approved" WHERE _id = ?', (order_id,))
    conn.commit()
    conn.close()
    logger.info(f"✅ Order approved: {order_id}")

async def reject_order(order_id):
    """Reject/cancel order"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = "rejected" WHERE _id = ?', (order_id,))
    conn.commit()
    conn.close()
    logger.info(f"❌ Order rejected: {order_id}")


# ═══════════════════════════════════════════════════════════════════
# 🔥 SESSION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def create_otp_session(order_id, user_id, account_id):
    """Create OTP session for reveal number"""
    import uuid
    _id = f"sess_{uuid.uuid4().hex[:8]}"
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO sessions (_id, order_id, user_id, account_id, created_at, expires_at)
                 VALUES (?, ?, ?, ?, ?, ?)''', (_id, order_id, user_id, account_id, 
                 datetime.now().isoformat(), 
                 (datetime.now().timestamp() + 300)))  # 5 min expiry
    conn.commit()
    conn.close()
    logger.info(f"✅ Session created: {_id}")
    return _id

async def get_session(session_id):
    """Get session by ID"""
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT * FROM sessions WHERE _id = ?', (session_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "_id": row[0],
            "order_id": row[1],
            "user_id": row[2],
            "account_id": row[3],
            "created_at": row[4],
            "expires_at": row[5]
        }
    return None


# ═══════════════════════════════════════════════════════════════════
# 🔥 STATS FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

async def get_stats():
    """Get bot statistics"""
    conn = get_conn()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM users')
    users = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orders')
    orders = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orders WHERE status = "approved"')
    approved = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"')
    pending = c.fetchone()[0]
    
    c.execute('SELECT SUM(amount) FROM orders WHERE status = "approved"')
    revenue = c.fetchone()[0] or 0.0
    
    conn.close()
    return {
        "users": users,
        "orders": orders,
        "approved": approved,
        "pending": pending,
        "revenue": revenue
    }


# ═══════════════════════════════════════════════════════════════════
# 🔥 DB CHECKER OBJECT (for payment_checker.py)
# ═══════════════════════════════════════════════════════════════════

class DatabaseChecker:
    @staticmethod
    async def check_connection():
        """Check database connection"""
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute('SELECT 1')
            conn.close()
            return {"ok": True, "message": "✅ Database connected"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

db_checker = DatabaseChecker()
