from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.schedule import Schedule
from app.models.user import User
from app.schemas.schedule import ScheduleCreate, ScheduleRead, ScheduleUpdate


router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleRead])
def list_schedules(db: Session = Depends(get_db)) -> list[Schedule]:
	return list(db.scalars(select(Schedule).order_by(Schedule.day_of_week.asc(), Schedule.start_time.asc())).all())


@router.get("/{schedule_id}", response_model=ScheduleRead)
def get_schedule(schedule_id: UUID, db: Session = Depends(get_db)) -> Schedule:
	schedule = db.get(Schedule, schedule_id)
	if schedule is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado")
	return schedule


@router.post("", response_model=ScheduleRead, status_code=status.HTTP_201_CREATED)
def create_schedule(payload: ScheduleCreate, db: Session = Depends(get_db)) -> Schedule:
	user = db.get(User, payload.user_id)
	if user is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
	if payload.end_time <= payload.start_time:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time debe ser posterior a start_time")

	schedule = Schedule(**payload.model_dump())
	db.add(schedule)
	db.flush()
	return schedule


@router.patch("/{schedule_id}", response_model=ScheduleRead)
def update_schedule(schedule_id: UUID, payload: ScheduleUpdate, db: Session = Depends(get_db)) -> Schedule:
	schedule = db.get(Schedule, schedule_id)
	if schedule is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado")

	data = payload.model_dump(exclude_unset=True)
	for field, value in data.items():
		setattr(schedule, field, value)

	if schedule.end_time <= schedule.start_time:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_time debe ser posterior a start_time")

	db.flush()
	return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(schedule_id: UUID, db: Session = Depends(get_db)) -> None:
	schedule = db.get(Schedule, schedule_id)
	if schedule is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horario no encontrado")

	db.delete(schedule)
	db.flush()