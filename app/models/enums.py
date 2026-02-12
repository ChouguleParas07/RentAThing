from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    RENTER = "RENTER"
    OWNER = "OWNER"
    ADMIN = "ADMIN"


class BookingStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EscrowStatus(str, enum.Enum):
    PENDING = "PENDING"
    HELD = "HELD"
    RELEASED = "RELEASED"
    CANCELLED = "CANCELLED"

