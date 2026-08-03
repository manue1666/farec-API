from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Attendance(Base):
	__tablename__ = "attendance"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
	check_in: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	check_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	department: Mapped[str] = mapped_column(String(120), nullable=False)
	date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

	user: Mapped["User"] = relationship(back_populates="attendance_records")