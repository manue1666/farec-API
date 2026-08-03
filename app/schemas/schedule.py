from __future__ import annotations

from datetime import time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ScheduleBase(BaseModel):
	user_id: UUID
	day_of_week: int = Field(ge=0, le=6)
	start_time: time
	end_time: time


class ScheduleCreate(ScheduleBase):
	pass


class ScheduleUpdate(BaseModel):
	day_of_week: int | None = Field(default=None, ge=0, le=6)
	start_time: time | None = None
	end_time: time | None = None


class ScheduleRead(ScheduleBase):
	id: UUID

	model_config = ConfigDict(from_attributes=True)