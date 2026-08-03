from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
	user_id: UUID
	type: str = Field(min_length=1, max_length=50)
	start_date: date
	end_date: date
	status: str = Field(default="pending", min_length=1, max_length=20)


class PermissionCreate(PermissionBase):
	pass


class PermissionUpdate(BaseModel):
	type: str | None = Field(default=None, min_length=1, max_length=50)
	start_date: date | None = None
	end_date: date | None = None
	status: str | None = Field(default=None, min_length=1, max_length=20)


class PermissionRead(PermissionBase):
	id: UUID
	created_at: datetime

	model_config = ConfigDict(from_attributes=True)