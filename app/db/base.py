from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.attendance import Attendance  # noqa: E402,F401
from app.models.face_encoding import FaceEncoding  # noqa: E402,F401
from app.models.permission import Permission  # noqa: E402,F401
from app.models.schedule import Schedule  # noqa: E402,F401
from app.models.user import User  # noqa: E402,F401


__all__ = ["Base", "User", "FaceEncoding", "Attendance", "Schedule", "Permission"]