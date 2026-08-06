from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.face_verification import FaceVerificationResult
from app.schemas.user import UserRead
from app.services.face_verification import face_verification_service


router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)) -> list[User]:
	return list(db.scalars(select(User).order_by(User.created_at.desc())).all())


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
	email: str = Form(...),
	full_name: str = Form(...),
	department: str = Form(...),
	is_admin: bool = Form(False),
	images: list[UploadFile] = File(...),
	db: Session = Depends(get_db),
) -> User:
	existing_user = db.scalar(select(User).where(User.email == email))
	if existing_user is not None:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un usuario con ese correo")

	user = User(email=email, full_name=full_name, department=department, is_admin=is_admin)
	db.add(user)
	db.flush()

	face_verification_service.ingest_user_dataset(db, user.id, images)
	db.refresh(user)
	return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
	user_id: UUID,
	email: str | None = Form(default=None),
	full_name: str | None = Form(default=None),
	department: str | None = Form(default=None),
	is_admin: bool | None = Form(default=None),
	db: Session = Depends(get_db),
) -> User:
	user = db.get(User, user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

	if email is not None:
		existing_user = db.scalar(select(User).where(User.email == email, User.id != user_id))
		if existing_user is not None:
			raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un usuario con ese correo")
		user.email = email
	if full_name is not None:
		user.full_name = full_name
	if department is not None:
		user.department = department
	if is_admin is not None:
		user.is_admin = is_admin

	db.flush()
	db.refresh(user)
	return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: Session = Depends(get_db)) -> None:
	user = db.get(User, user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

	db.delete(user)
	db.flush()


@router.post("/{user_id}/face-dataset", status_code=status.HTTP_201_CREATED)
def append_face_dataset(
	user_id: UUID,
	images: list[UploadFile] = File(...),
	db: Session = Depends(get_db),
) -> dict[str, object]:
	user = db.get(User, user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

	records = face_verification_service.ingest_user_dataset(db, user.id, images)
	return {"user_id": str(user.id), "stored_samples": len(records)}


@router.post("/verify-face", response_model=FaceVerificationResult)
def verify_face(
	image: UploadFile = File(...),
	db: Session = Depends(get_db),
) -> FaceVerificationResult:
	result = face_verification_service.verify_face(db, image)
	return FaceVerificationResult.model_validate(result)