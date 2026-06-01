from decimal import Decimal
import asyncio
from typing import Optional
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet
from app.schemas import OperationType


class WalletNotFoundError(Exception):
    """Raised when a wallet with the given UUID does not exist."""
    pass


class InsufficientFundsError(Exception):
    """Raised when a withdrawal is attempted with insufficient balance."""
    pass


# Memory locks for SQLite concurrency testing
_wallet_locks = {}
_locks_mutex = asyncio.Lock()


async def get_wallet_lock(wallet_id: uuid.UUID) -> asyncio.Lock:
    """Get or create an asyncio.Lock for a specific wallet UUID."""
    async with _locks_mutex:
        if wallet_id not in _wallet_locks:
            _wallet_locks[wallet_id] = asyncio.Lock()
        return _wallet_locks[wallet_id]


async def get_wallet(db: AsyncSession, wallet_id: uuid.UUID, lock: bool = False) -> Optional[Wallet]:
    """
    Retrieve a wallet by its UUID.
    
    If lock=True, applies a pessimistic lock (SELECT ... FOR UPDATE) 
    to prevent concurrent modifications on this wallet row.
    """
    query = select(Wallet).filter(Wallet.id == wallet_id)
    if lock:
        query = query.with_for_update()
    
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _execute_operation_impl(
    db: AsyncSession,
    wallet_id: uuid.UUID,
    operation_type: OperationType,
    amount: Decimal
) -> Wallet:
    """Internal implementation of wallet operation."""
    wallet = await get_wallet(db, wallet_id, lock=True)
    if not wallet:
        raise WalletNotFoundError()

    if operation_type == OperationType.DEPOSIT:
        wallet.balance += amount
    elif operation_type == OperationType.WITHDRAW:
        if wallet.balance < amount:
            raise InsufficientFundsError()
        wallet.balance -= amount

    await db.commit()
    await db.refresh(wallet)
    return wallet


async def execute_wallet_operation(
    db: AsyncSession,
    wallet_id: uuid.UUID,
    operation_type: OperationType,
    amount: Decimal
) -> Wallet:
    """
    Execute deposit or withdrawal on a wallet securely.
    
    Uses database-level pessimistic locking (SELECT FOR UPDATE) in PostgreSQL.
    Falls back to in-memory asyncio locking in SQLite (used for testing).
    """
    is_sqlite = db.bind.dialect.name == "sqlite"

    if is_sqlite:
        lock = await get_wallet_lock(wallet_id)
        async with lock:
            return await _execute_operation_impl(db, wallet_id, operation_type, amount)
    
    return await _execute_operation_impl(db, wallet_id, operation_type, amount)


async def create_wallet(db: AsyncSession, balance: Decimal = Decimal("0.00")) -> Wallet:
    """
    Create a new wallet with an optional initial balance.
    """
    wallet = Wallet(balance=balance)
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)
    return wallet
