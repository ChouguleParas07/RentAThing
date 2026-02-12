from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import EscrowStatus


class EscrowRead(BaseModel):
    id: UUID
    booking_id: UUID
    renter_id: UUID
    owner_id: UUID
    item_id: UUID
    amount_held: Decimal
    amount_released: Decimal
    damage_fee: Decimal
    status: EscrowStatus

    model_config = {"from_attributes": True}


class EscrowSettleRequest(BaseModel):
    damage_fee: Decimal = Field(ge=0)

