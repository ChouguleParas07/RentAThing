from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_active_user
from app.db.session import get_db_session
from app.models.enums import BookingStatus, UserRole
from app.schemas.auth import AuthenticatedUser
from app.schemas.booking import BookingCreate, BookingListResponse, BookingRead
from app.services.booking_service import BookingService


router = APIRouter(prefix="/bookings", tags=["bookings"])


def get_booking_service(db: Annotated[AsyncSession, Depends(get_db_session)]) -> BookingService:
    return BookingService(db)


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingRead:
    try:
        return await service.create_booking(renter_id=current_user.id, payload=payload)
    except (ValueError, PermissionError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/me/renter", response_model=BookingListResponse)
async def list_my_renter_bookings(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[BookingService, Depends(get_booking_service)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> BookingListResponse:
    return await service.list_bookings_for_renter(renter_id=current_user.id, skip=skip, limit=limit)


@router.get("/me/owner", response_model=BookingListResponse)
async def list_my_owner_bookings(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[BookingService, Depends(get_booking_service)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> BookingListResponse:
    if current_user.role not in (UserRole.OWNER, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owners can view owner bookings")
    return await service.list_bookings_for_owner(owner_id=current_user.id, skip=skip, limit=limit)


@router.patch("/{booking_id}/status", response_model=BookingRead)
async def update_booking_status(
    booking_id: UUID,
    new_status: BookingStatus,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_active_user)],
    service: Annotated[BookingService, Depends(get_booking_service)],
) -> BookingRead:
    try:
        return await service.update_status(
            booking_id=booking_id,
            actor_id=current_user.id,
            role=current_user.role,
            new_status=new_status,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

