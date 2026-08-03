from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
	email: EmailStr
	full_name: str = Field(min_length=1, max_length=255)
	department: str = Field(min_length=1, max_length=120)
	is_admin: bool = False


class UserCreate(UserBase):
	pass


class UserUpdate(BaseModel):
	email: EmailStr | None = None
	full_name: str | None = Field(default=None, min_length=1, max_length=255)
	department: str | None = Field(default=None, min_length=1, max_length=120)
	is_admin: bool | None = None


class UserRead(UserBase):
	id: UUID
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)