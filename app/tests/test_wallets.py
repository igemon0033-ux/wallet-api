import asyncio
from decimal import Decimal
import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_wallet(async_client: AsyncClient):
    response = await async_client.post("/api/v1/wallets")
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert Decimal(data["balance"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_get_wallet_balance(async_client: AsyncClient):
    create_resp = await async_client.post("/api/v1/wallets")
    wallet_id = create_resp.json()["id"]

    response = await async_client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == wallet_id
    assert Decimal(data["balance"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_get_wallet_balance_not_found(async_client: AsyncClient):
    random_uuid = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/wallets/{random_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"


@pytest.mark.asyncio
async def test_deposit_operation(async_client: AsyncClient):
    create_resp = await async_client.post("/api/v1/wallets")
    wallet_id = create_resp.json()["id"]

    response = await async_client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1500.50}
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["balance"]) == Decimal("1500.50")


@pytest.mark.asyncio
async def test_withdraw_operation(async_client: AsyncClient):
    create_resp = await async_client.post("/api/v1/wallets")
    wallet_id = create_resp.json()["id"]

    await async_client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000}
    )

    response = await async_client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 400.25}
    )
    assert response.status_code == 200
    data = response.json()
    assert Decimal(data["balance"]) == Decimal("599.75")


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(async_client: AsyncClient):
    create_resp = await async_client.post("/api/v1/wallets")
    wallet_id = create_resp.json()["id"]

    await async_client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 100}
    )

    response = await async_client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 150}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"


@pytest.mark.asyncio
async def test_operation_invalid_wallet_not_found(async_client: AsyncClient):
    random_uuid = str(uuid.uuid4())
    response = await async_client.post(
        f"/api/v1/wallets/{random_uuid}/operation",
        json={"operation_type": "DEPOSIT", "amount": 100}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"


@pytest.mark.asyncio
async def test_validation_negative_amount(async_client: AsyncClient):
    create_resp = await async_client.post("/api/v1/wallets")
    wallet_id = create_resp.json()["id"]

    response = await async_client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": -100}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validation_too_many_decimals(async_client: AsyncClient):
    create_resp = await async_client.post("/api/v1/wallets")
    wallet_id = create_resp.json()["id"]

    response = await async_client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 10.555}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_concurrent_wallet_operations(async_client: AsyncClient):
    create_resp = await async_client.post("/api/v1/wallets")
    wallet_id = create_resp.json()["id"]

    await async_client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 1000}
    )

    tasks = []
    for _ in range(5):
        tasks.append(
            async_client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "DEPOSIT", "amount": 100}
            )
        )
        tasks.append(
            async_client.post(
                f"/api/v1/wallets/{wallet_id}/operation",
                json={"operation_type": "WITHDRAW", "amount": 50}
            )
        )

    responses = await asyncio.gather(*tasks)

    for resp in responses:
        assert resp.status_code == 200

    final_resp = await async_client.get(f"/api/v1/wallets/{wallet_id}")
    assert final_resp.status_code == 200
    assert Decimal(final_resp.json()["balance"]) == Decimal("1250.00")
