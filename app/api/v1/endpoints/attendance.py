from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.attendance import Attendance
from app.models.user import User
from app.schemas.attendance import AttendanceCreate, AttendanceFaceActionResult, AttendanceRead, AttendanceUpdate
from app.schemas.face_verification import FaceVerificationResult
from app.services.face_verification import face_verification_service


router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.get("", response_model=list[AttendanceRead])
def list_attendance(db: Session = Depends(get_db)) -> list[Attendance]:
	return list(db.scalars(select(Attendance).order_by(Attendance.date.desc(), Attendance.check_in.desc())).all())


@router.get("/{attendance_id}", response_model=AttendanceRead)
def get_attendance(attendance_id: UUID, db: Session = Depends(get_db)) -> Attendance:
	attendance = db.get(Attendance, attendance_id)
	if attendance is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia no encontrada")
	return attendance


@router.post("", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def create_attendance(payload: AttendanceCreate, db: Session = Depends(get_db)) -> Attendance:
	user = db.get(User, payload.user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

	attendance = Attendance(**payload.model_dump())
	db.add(attendance)
	db.flush()
	return attendance


@router.post("/check-in", response_model=AttendanceFaceActionResult, status_code=status.HTTP_201_CREATED)
def check_in_with_face(image: UploadFile = File(...), db: Session = Depends(get_db)) -> AttendanceFaceActionResult:
	verification = _verify_face_or_raise(db, image)
	user = _get_verified_user(db, verification)
	today = datetime.now(UTC).date()
	existing_attendance = db.scalar(
		select(Attendance).where(Attendance.user_id == user.id, Attendance.date == today)
	)
	if existing_attendance is not None:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un registro de asistencia para hoy")

	attendance = Attendance(
		user_id=user.id,
		check_in=datetime.now(UTC),
		check_out=None,
		department=user.department,
		date=today,
	)
	db.add(attendance)
	db.flush()
	return AttendanceFaceActionResult(
		authentication=verification,
		attendance=AttendanceRead.model_validate(attendance),
		action="check_in",
		message="Entrada registrada correctamente",
	)


@router.post("/check-out", response_model=AttendanceFaceActionResult)
def check_out_with_face(image: UploadFile = File(...), db: Session = Depends(get_db)) -> AttendanceFaceActionResult:
	verification = _verify_face_or_raise(db, image)
	user = _get_verified_user(db, verification)
	today = datetime.now(UTC).date()
	attendance = db.scalar(
		select(Attendance).where(
			Attendance.user_id == user.id,
			Attendance.date == today,
			Attendance.check_out.is_(None),
		)
	)
	if attendance is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró una entrada abierta para hoy")

	attendance.check_out = datetime.now(UTC)
	db.flush()
	return AttendanceFaceActionResult(
		authentication=verification,
		attendance=AttendanceRead.model_validate(attendance),
		action="check_out",
		message="Salida registrada correctamente",
	)


@router.get("/users/{user_id}/history", response_model=list[AttendanceRead])
def get_user_history(
	user_id: UUID,
	year: int | None = None,
	month: int | None = None,
	week: int | None = None,
	db: Session = Depends(get_db),
) -> list[Attendance]:
	query = select(Attendance).where(Attendance.user_id == user_id)
	query = _apply_date_filters(query, year=year, month=month, week=week)
	return list(db.scalars(query.order_by(Attendance.date.desc(), Attendance.check_in.desc())).all())


@router.get("/areas/{department}/history", response_model=list[AttendanceRead])
def get_area_history(
	department: str,
	year: int | None = None,
	month: int | None = None,
	week: int | None = None,
	db: Session = Depends(get_db),
) -> list[Attendance]:
	query = select(Attendance).where(Attendance.department == department)
	query = _apply_date_filters(query, year=year, month=month, week=week)
	return list(db.scalars(query.order_by(Attendance.date.desc(), Attendance.check_in.desc())).all())


@router.patch("/{attendance_id}", response_model=AttendanceRead)
def update_attendance(attendance_id: UUID, payload: AttendanceUpdate, db: Session = Depends(get_db)) -> Attendance:
	attendance = db.get(Attendance, attendance_id)
	if attendance is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia no encontrada")

	data = payload.model_dump(exclude_unset=True)
	for field, value in data.items():
		setattr(attendance, field, value)

	if attendance.check_out is not None and attendance.check_out < attendance.check_in:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="check_out no puede ser anterior a check_in")

	db.flush()
	return attendance


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(attendance_id: UUID, db: Session = Depends(get_db)) -> None:
	attendance = db.get(Attendance, attendance_id)
	if attendance is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asistencia no encontrada")

	db.delete(attendance)
	db.flush()


def _verify_face_or_raise(db: Session, image: UploadFile) -> FaceVerificationResult:
	result = face_verification_service.verify_face(db, image)
	verification = FaceVerificationResult.model_validate(result)
	if not verification.matched or verification.user_id is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No coincide con ningún usuario registrado")
	return verification


def _get_verified_user(db: Session, verification: FaceVerificationResult) -> User:
	user = db.get(User, verification.user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
	return user


def _apply_date_filters(query, *, year: int | None, month: int | None, week: int | None):
	if year is not None:
		query = query.where(func.extract("year", Attendance.date) == year)
	if month is not None:
		query = query.where(func.extract("month", Attendance.date) == month)
	if week is not None:
		query = query.where(func.extract("week", Attendance.date) == week)
	return query