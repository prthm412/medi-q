import uuid
from datetime import date

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    dob: Mapped[date] = mapped_column(nullable=False)
    contact_info: Mapped[str] = mapped_column(nullable=False)

    user = relationship("User")