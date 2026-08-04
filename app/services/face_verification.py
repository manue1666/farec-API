from __future__ import annotations

import tempfile
import pickle
import shutil
from pathlib import Path
from uuid import UUID, uuid4

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.face_encoding import FaceEncoding

from deepface import DeepFace
from deepface.modules.exceptions import FaceNotDetected



class FaceVerificationService:
	match_threshold: float = 0.4
	detector_backend: str = "opencv"

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

		self._ensure_opencv_cascades()

		try:
			result = DeepFace.represent(
				img_path=str(image_path),
				model_name="Facenet512",
				detector_backend=self.detector_backend,
				enforce_detection=True,
			)
		except FaceNotDetected as exc:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="No se detectó un rostro válido en la imagen",
			) from exc

		if not result:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se detectó un rostro válido en la imagen")

		first_result = result[0] if isinstance(result, list) else result
		return list(first_result["embedding"])

	def verify_face(self, db: Session, image: UploadFile) -> dict[str, object]:
		active_encodings = list(
			db.scalars(select(FaceEncoding).where(FaceEncoding.is_active.is_(True))).all()
		)
		if not active_encodings:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="No hay rostros registrados para comparar",
			)

		probe_path = self._store_temporary_upload(image)
		try:
			probe_embedding = self._normalize_embedding(self._extract_encoding(probe_path))
			best_match: tuple[FaceEncoding, float] | None = None

			for record in active_encodings:
				stored_embedding = self._normalize_embedding(pickle.loads(record.encoding))
				distance = self._cosine_distance(probe_embedding, stored_embedding)
				if best_match is None or distance < best_match[1]:
					best_match = (record, distance)

			if best_match is None:
				raise HTTPException(
					status_code=status.HTTP_404_NOT_FOUND,
					detail="No se encontró una coincidencia facial",
				)

			record, best_distance = best_match
			is_match = best_distance <= self.match_threshold
			return {
				"matched": is_match,
				"user_id": record.user_id if is_match else None,
				"face_encoding_id": record.id if is_match else None,
				"distance": best_distance,
				"threshold": self.match_threshold,
			}
		finally:
			probe_path.unlink(missing_ok=True)

	def _store_temporary_upload(self, image: UploadFile) -> Path:
		extension = Path(image.filename or "").suffix or ".jpg"
		with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
			shutil.copyfileobj(image.file, temp_file)
			return Path(temp_file.name)

	def _normalize_embedding(self, embedding: list[float]) -> np.ndarray:
		vector = np.array(embedding, dtype=np.float32)
		norm = np.linalg.norm(vector)
		if norm == 0:
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail="No se pudo normalizar el embedding facial",
			)
		return vector / norm

	def _cosine_distance(self, first: np.ndarray, second: np.ndarray) -> float:
		return float(1.0 - np.dot(first, second))

	def _ensure_opencv_cascades(self) -> None:
		runtime_cascade_dir = Path(cv2.__file__).resolve().parent / "data"
		runtime_cascade_dir.mkdir(parents=True, exist_ok=True)

		project_cascade_dir = Path(__file__).resolve().parents[1] / "cascades"

		required_files = {
			"haarcascade_frontalface_default.xml": [project_cascade_dir],
			"haarcascade_eye.xml": [project_cascade_dir],
		}

		missing_files: list[str] = []
		for file_name, source_dirs in required_files.items():
			destination_file = runtime_cascade_dir / file_name
			if destination_file.exists():
				continue

			source_file = next((directory / file_name for directory in source_dirs if (directory / file_name).exists()), None)
			if source_file is None:
				missing_files.append(file_name)
				continue

			shutil.copy2(source_file, destination_file)

		if missing_files:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail=f"Faltan archivos cascade requeridos: {', '.join(missing_files)}",
			)


face_verification_service = FaceVerificationService()