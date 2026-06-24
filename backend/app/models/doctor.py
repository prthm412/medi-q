import uuid
from datetime import time

from sqlalchemy import ForeignKey, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    specialization: Mapped[str] = mapped_column(nullable=False)
    working_hours_start: Mapped[time] = mapped_column(Time, nullable=False)
    working_hours_end: Mapped[time] = mapped_column(Time, nullable=False)
    max_daily_patients: Mapped[int] = mapped_column(nullable=False)

    user = relationship("User")