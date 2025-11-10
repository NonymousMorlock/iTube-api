import enum
import uuid

from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.core.database import Base


class VisibilityStatus(enum.Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    UNLISTED = "UNLISTED"


class ProcessingStatus(enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Video(Base):
    __tablename__ = 'videos'

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.cognito_sub'), nullable=False)
    video_s3_key: Mapped[str] = mapped_column(nullable=False)
    visibility: Mapped[VisibilityStatus] = mapped_column(
        Enum(VisibilityStatus),
        default=VisibilityStatus.PRIVATE,
        nullable=False,
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus),
        default=ProcessingStatus.IN_PROGRESS,
        nullable=False,
    )
