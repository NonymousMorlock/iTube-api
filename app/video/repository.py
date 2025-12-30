import logging
from typing import Sequence, Optional

from botocore.client import BaseClient
from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import InternalServerError, NotFoundError
from app.video.models import Video, VisibilityStatus, ProcessingStatus

logger = logging.getLogger(__name__)


class VideoRepository:
    def __init__(self, s3: BaseClient, database: Session):
        self.s3 = s3
        self.db = database

    async def generate_presigned_video_url(self, video_id: str) -> str:
        try:
            presigned_url = self.s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.S3_RAW_VIDEOS_BUCKET,
                    'Key': video_id,
                    # 'ACL': 'private',
                    'ContentType': 'video/mp4',
                },
                # ExpiresIn=3600 # URL valid for 1 hour
            )
            return presigned_url
        except ClientError as e:
            raise _generate_s3_error(e, operation='generate_presigned_url')

    async def generate_presigned_thumbnail_url(self, thumbnail_id: str) -> str:
        try:
            presigned_url = self.s3.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': settings.S3_VIDEO_THUMBNAILS_BUCKET,
                    'Key': thumbnail_id,
                    'ACL': 'public-read',
                    'ContentType': 'image/jpg',
                },
                # ExpiresIn=3600 # URL valid for 1 hour
            )
            return presigned_url
        except ClientError as e:
            raise _generate_s3_error(e, operation='generate_presigned_url')

    async def save_video_metadata(
            self,
            user_id: str,
            title: str,
            description: str,
            video_s3_key: str,
            visibility: str,
    ) -> Video:
        try:
            video = Video(
                title=title,
                description=description,
                user_id=user_id,
                video_s3_key=video_s3_key,
                visibility=VisibilityStatus[visibility],
            )
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            return video
        except SQLAlchemyError as e:
            self.db.rollback()
            raise _generate_database_error(e, operation='save_video_metadata')

    async def get_all_videos(self) -> Sequence[Video]:
        statement = (
            select(Video)
            .where(Video.processing_status == ProcessingStatus.COMPLETED)
            .where(Video.visibility == VisibilityStatus.PUBLIC)

        )

        videos = self.db.execute(statement).scalars().all()
        return videos

    async def get_video_by_id(self, video_id: str) -> Optional[Video]:
        statement = (
            select(Video)
            .where(Video.id == video_id)
            .where(Video.processing_status == ProcessingStatus.COMPLETED)
            .where(Video.visibility.in_([VisibilityStatus.PUBLIC, VisibilityStatus.UNLISTED]))
            .limit(1)
        )

        return self.db.execute(statement).scalar_one_or_none()

    async def get_video_by_s3_key(self, s3_key: str) -> Optional[Video]:
        statement = (
            select(Video)
            .where(Video.video_s3_key == s3_key)
            .limit(1)
        )
        return self.db.execute(statement).scalar_one_or_none()

    async def update_video_processing_status(self, video_id: str, status: ProcessingStatus) -> None:
        try:
            statement = (
                select(Video)
                .where(Video.id == video_id)
                .limit(1)
            )
            video = self.db.execute(statement).scalar_one_or_none()
            if not video:
                raise NotFoundError("Video not found")

            video.processing_status = status
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            raise _generate_database_error(e, operation='update_video_processing_status')


def _generate_s3_error(exception: ClientError, operation: str = 'operation') -> InternalServerError:
    """Convert S3 ClientError to AppError."""
    error = exception.response.get("Error", {})
    code = error.get("Code", 'Unknown')
    message = error.get("Message", str(exception))

    logger.error(
        f"S3 {operation} failed",
        extra={"s3_error_code": code, "s3_error_message": message},
        exc_info=exception,
    )
    return InternalServerError(f"S3 operation failed: {message}", error_code=code)


def _generate_database_error(exception: SQLAlchemyError, operation: str = 'operation') -> InternalServerError:
    """Convert SQLAlchemy error to AppError."""
    error_message = str(exception)
    logger.error(
        f"Database {operation} failed",
        extra={"db_error": error_message},
        exc_info=exception,
    )
    return InternalServerError(f"Database operation failed", error_code='DATABASE_ERROR')
