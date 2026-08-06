from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.permission import Permission
from app.models.user import User
from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate


router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=list[PermissionRead])
def list_permissions(db: Session = Depends(get_db)) -> list[Permission]:
	return list(db.scalars(select(Permission).order_by(Permission.created_at.desc())).all())


@router.get("/history", response_model=list[PermissionRead])
def get_permission_history(
	user_id: UUID | None = None,
	status_filter: str | None = None,
	db: Session = Depends(get_db),
) -> list[Permission]:
	query = select(Permission)
	if user_id is not None:
		query = query.where(Permission.user_id == user_id)
	if status_filter is not None:
		query = query.where(Permission.status == status_filter)
	return list(db.scalars(query.order_by(Permission.created_at.desc())).all())


@router.get("/{permission_id}", response_model=PermissionRead)
def get_permission(permission_id: UUID, db: Session = Depends(get_db)) -> Permission:
	permission = db.get(Permission, permission_id)
	if permission is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permiso no encontrado")
	return permission


@router.post("", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
def create_permission(payload: PermissionCreate, db: Session = Depends(get_db)) -> Permission:
	user = db.get(User, payload.user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
	if payload.end_date < payload.start_date:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date no puede ser anterior a start_date")

	permission = Permission(**payload.model_dump())
	db.add(permission)
	db.flush()
	return permission


@router.patch("/{permission_id}", response_model=PermissionRead)
def update_permission(permission_id: UUID, payload: PermissionUpdate, db: Session = Depends(get_db)) -> Permission:
	permission = db.get(Permission, permission_id)
	if permission is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permiso no encontrado")

	data = payload.model_dump(exclude_unset=True)
	for field, value in data.items():
		setattr(permission, field, value)

	if permission.end_date < permission.start_date:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_date no puede ser anterior a start_date")

	db.flush()
	return permission


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: UUID, db: Session = Depends(get_db)) -> None:
	permission = db.get(Permission, permission_id)
	if permission is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permiso no encontrado")

	db.delete(permission)
	db.flush()