from decimal import Decimal
from enum import Enum
import uuid
from pydantic import BaseModel, Field, field_validator


class OperationType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperationRequest(BaseModel):
    operation_type: OperationType
    amount: Decimal = Field(..., gt=0, description="Amount must be greater than 0")

    @field_validator("amount")
    @classmethod
    def validate_decimal_places(cls, value: Decimal) -> Decimal:
        if value.as_tuple().exponent < -2:
            raise ValueError("Amount cannot have more than 2 decimal places")
        return value


class WalletResponse(BaseModel):
    id: uuid.UUID
    balance: Decimal

    model_config = {
        "from_attributes": True
    }
