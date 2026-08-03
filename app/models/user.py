from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
	__tablename__ = "users"

	id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
	email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
	full_name: Mapped[str] = mapped_column(String(255), nullable=False)
	department: Mapped[str] = mapped_column(String(120), nullable=False)
	is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

	face_encodings: Mapped[list["FaceEncoding"]] = relationship(back_populates="user", cascade="all, delete-orphan")
	attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="user", cascade="all, delete-orphan")
	schedules: Mapped[list["Schedule"]] = relationship(back_populates="user", cascade="all, delete-orphan")
	permissions: Mapped[list["Permission"]] = relationship(back_populates="user", cascade="all, delete-orphan")