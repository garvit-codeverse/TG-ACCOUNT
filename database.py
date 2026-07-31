from __future__ import annotations
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, Boolean, Text, select
from datetime import datetime
from config import DATABASE_URL

# ---------- ENGINE ----------
if "postgresql" in DATABASE_URL:
    if "+" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
else:
    engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# ---------- TABLES ----------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    session_string = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String, unique=True, nullable=False)
    session_string = Column(Text, nullable=True)
    password = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    is_sold = Column(Boolean, default=False)
    price = Column(Float, default=0.0)
    added_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Deposit(Base):
    __tablename__ = "deposits"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")
    txn_id = Column(String, unique=True, nullable=True)
    upi_ref = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

class PaymentLog(Base):
    __tablename__ = "payment_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    amount = Column(Float, nullable=False)
    txn_id = Column(String, nullable=True)
    status = Column(String, default="initiated")
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ---------- INIT ----------
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created/verified.")

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

# ---------- CRUD ----------
async def get_user_by_tg_id(tg_id: int, db: AsyncSession):
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    return result.scalar_one_or_none()

# ✅ FIXED FUNCTION (db pehle, optional baad mein)
async def create_user(tg_id: int, db: AsyncSession, username: str = None, first_name: str = None):
    user = User(tg_id=tg_id, username=username, first_name=first_name)
    db.add(user)
    await db.commit()
    return user

async def add_deposit(user_id: int, amount: float, txn_id: str, db: AsyncSession):
    dep = Deposit(user_id=user_id, amount=amount, txn_id=txn_id, status="pending")
    db.add(dep)
    await db.commit()
    return dep

async def update_deposit_status(txn_id: str, status: str, db: AsyncSession):
    result = await db.execute(select(Deposit).where(Deposit.txn_id == txn_id))
    dep = result.scalar_one_or_none()
    if dep:
        dep.status = status
        if status == "confirmed":
            dep.confirmed_at = datetime.utcnow()
            user = await get_user_by_tg_id(dep.user_id, db)
            if user:
                user.balance += dep.amount
        await db.commit()
        return dep
    return None

async def save_session(tg_id: int, session_string: str, phone: str, db: AsyncSession):
    result = await db.execute(select(UserSession).where(UserSession.user_id == tg_id))
    sess = result.scalar_one_or_none()
    if sess:
        sess.session_string = session_string
        sess.phone = phone
    else:
        sess = UserSession(user_id=tg_id, session_string=session_string, phone=phone)
        db.add(sess)
    await db.commit()
    return sess

async def get_session_by_user(tg_id: int, db: AsyncSession):
    result = await db.execute(select(UserSession).where(UserSession.user_id == tg_id))
    return result.scalar_one_or_none()

async def get_all_accounts(db: AsyncSession, sold: bool = False):
    result = await db.execute(select(Account).where(Account.is_sold == sold).order_by(Account.created_at.desc()))
    return result.scalars().all()

async def add_account(phone: str, session_string: str, price: float, added_by: int, db: AsyncSession):
    acc = Account(phone=phone, session_string=session_string, price=price, added_by=added_by, is_sold=False)
    db.add(acc)
    await db.commit()
    return acc

async def mark_account_sold(account_id: int, db: AsyncSession):
    result = await db.execute(select(Account).where(Account.id == account_id))
    acc = result.scalar_one_or_none()
    if acc:
        acc.is_sold = True
        await db.commit()
    return acc

async def add_balance(tg_id: int, amount: float, db: AsyncSession):
    result = await db.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user:
        user.balance = user.balance + amount
        await db.commit()
        return user
    return None
