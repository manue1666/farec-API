from __future__ import annotations

import pickle
import shutil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.face_encoding import FaceEncoding

try:
	from deepface import DeepFace
except ImportError:  # pragma: no cover - optional dependency until installed locally
	DeepFace = None


class FaceVerificationService:
	def __init__(self, storage_dir: Path | None = None) -> None:
		self.storage_dir = storage_dir or settings.face_storage_dir

	def ingest_user_dataset(self, db: Session, user_id: UUID, images: list[UploadFile]) -> list[FaceEncoding]:
		if not images:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Se requiere al menos una imagen para el dataset facial")

		user_dir = self.storage_dir / str(user_id)
		user_dir.mkdir(parents=True, exist_ok=True)

		records: list[FaceEncoding] = []
		saved_paths: list[Path] = []

		try:
			for image in images:
				stored_path = self._store_upload(image, user_dir)
				saved_paths.append(stored_path)
				encoding = self._extract_encoding(stored_path)
				record = FaceEncoding(
					user_id=user_id,
					encoding=pickle.dumps(encoding),
					image_path=str(stored_path),
					is_active=True,
				)
				db.add(record)
				records.append(record)

			db.flush()
			return records
		except Exception:
			for path in saved_paths:
				path.unlink(missing_ok=True)
			raise

	def _store_upload(self, image: UploadFile, destination_dir: Path) -> Path:
		extension = Path(image.filename or "").suffix or ".jpg"
		stored_path = destination_dir / f"{uuid4()}{extension}"
		with stored_path.open("wb") as buffer:
			shutil.copyfileobj(image.file, buffer)
		return stored_path

	def _extract_encoding(self, image_path: Path) -> list[float]:
		if DeepFace is None:
			raise HTTPException(
				status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
				detail="DeepFace no está instalado en el entorno actual",
			)

		result = DeepFace.represent(
			img_path=str(image_path),
			model_name="Facenet512",
			detector_backend="opencv",
			enforce_detection=True,
		)

		if not result:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se detectó un rostro válido en la imagen")

		first_result = result[0] if isinstance(result, list) else result
		return list(first_result["embedding"])


face_verification_service = FaceVerificationService()