from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.face_verification import FaceVerificationResult


class AttendanceCreate(BaseModel):
	user_id: UUID
	department: str
	check_in: datetime
	check_out: datetime | None = None
	date: date


class AttendanceUpdate(BaseModel):
	check_out: datetime | None = None
	department: str | None = None


class AttendanceRead(AttendanceCreate):
	id: UUID

	model_config = ConfigDict(from_attributes=True)


class AttendanceFaceActionResult(BaseModel):
	authentication: FaceVerificationResult
	attendance: AttendanceRead
	action: str
	message: str

	model_config = ConfigDict(from_attributes=True)