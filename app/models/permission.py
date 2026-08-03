from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Permission(Base):
	__tablename__ = "permissions"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
	user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
	type: Mapped[str] = mapped_column(String(50), nullable=False)
	start_date: Mapped[date] = mapped_column(Date, nullable=False)
	end_date: Mapped[date] = mapped_column(Date, nullable=False)
	status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

	user: Mapped["User"] = relationship(back_populates="permissions")