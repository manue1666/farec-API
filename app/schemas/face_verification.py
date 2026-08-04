from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FaceVerificationResult(BaseModel):
	matched: bool
	user_id: UUID | None = None
	face_encoding_id: UUID | None = None
	distance: float
	threshold: float

	model_config = ConfigDict(from_attributes=True)