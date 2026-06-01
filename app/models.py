import uuid
from decimal import Decimal
from sqlalchemy import Numeric, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2),
        nullable=False,
        default=Decimal("0.00")
    )

    def __repr__(self) -> str:
        return f"<Wallet(id={self.id}, balance={self.balance})>"
