from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    slug: str
    description: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None


class CategoryRead(CategoryBase):
    id: UUID

    model_config = {"from_attributes": True}

