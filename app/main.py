from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, engine
from app.schemas import WalletOperationRequest, WalletResponse
from app.services import (
    get_wallet,
    execute_wallet_operation,
    create_wallet,
    WalletNotFoundError,
    InsufficientFundsError
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="User Wallets REST API",
    description="A concurrent and asynchronous REST API for user wallets",
    version="1.0.0",
    lifespan=lifespan
)


# Exception Handlers
@app.exception_handler(WalletNotFoundError)
async def wallet_not_found_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Wallet not found"}
    )


@app.exception_handler(InsufficientFundsError)
async def insufficient_funds_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Insufficient funds"}
    )


# API Endpoints
@app.post("/api/v1/wallets", response_model=WalletResponse, status_code=status.HTTP_201_CREATED, summary="Create a new wallet")
async def create_new_wallet(db: AsyncSession = Depends(get_db)):
    """Create a new wallet with zero balance."""
    return await create_wallet(db)


@app.get("/api/v1/wallets/{wallet_uuid}", response_model=WalletResponse, summary="Get wallet balance")
async def get_wallet_balance(wallet_uuid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get the current balance of the specified wallet."""
    wallet = await get_wallet(db, wallet_uuid)
    if not wallet:
        raise WalletNotFoundError()
    return wallet


@app.post("/api/v1/wallets/{wallet_uuid}/operation", response_model=WalletResponse, summary="Perform wallet operation")
async def perform_wallet_operation(
    wallet_uuid: uuid.UUID,
    operation: WalletOperationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform a deposit or withdrawal operation on the specified wallet.
    
    This endpoint is concurrency-safe and uses pessimistic locking to prevent race conditions.
    """
    return await execute_wallet_operation(
        db=db,
        wallet_id=wallet_uuid,
        operation_type=operation.operation_type,
        amount=operation.amount
    )
