from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.schemas.auth import AuthenticatedUser
from app.schemas.escrow import EscrowRead, EscrowSettleRequest
from app.services.escrow_service import EscrowService


router = APIRouter(prefix="/escrow", tags=["escrow"])


def get_escrow_service(db: Annotated[AsyncSession, Depends(get_db_session)]) -> EscrowService:
    return EscrowService(db)


@router.get("/bookings/{booking_id}", response_model=EscrowRead)
async def get_escrow_for_booking(
    booking_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[EscrowService, Depends(get_escrow_service)],
) -> EscrowRead:
    try:
        escrow = await service.get_for_booking(booking_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    # Basic visibility: both renter and owner (and admin) can see
    if current_user.role != UserRole.ADMIN and current_user.id not in (escrow.renter_id, escrow.owner_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not part of this escrow")
    return escrow


@router.post("/bookings/{booking_id}/cancel", response_model=EscrowRead)
async def cancel_escrow_for_booking(
    booking_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[EscrowService, Depends(get_escrow_service)],
) -> EscrowRead:
    try:
        escrow = await service.get_for_booking(booking_id)
        if current_user.role != UserRole.ADMIN and current_user.id not in (escrow.renter_id, escrow.owner_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not part of this escrow")
        return await service.cancel_for_booking(booking_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/bookings/{booking_id}/settle", response_model=EscrowRead)
async def settle_escrow_for_booking(
    booking_id: UUID,
    body: EscrowSettleRequest,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[EscrowService, Depends(get_escrow_service)],
) -> EscrowRead:
    try:
        return await service.settle_for_booking(
            booking_id=booking_id,
            actor_id=current_user.id,
            role=current_user.role,
            damage_fee=body.damage_fee,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

