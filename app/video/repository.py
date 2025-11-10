from typing import Sequence, Optional

from botocore.client import BaseClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.video.models import Video, VisibilityStatus, ProcessingStatus


class VideoRepository:
    def __init__(self, s3: BaseClient, database: Session):
        self.s3 = s3
        self.db = database

    async def generate_presigned_video_url(self, video_id: str) -> str:
        presigned_url = self.s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.S3_RAW_VIDEOS_BUCKET,
                'Key': video_id,
                # 'ACL': 'private',
                'ContentType': 'video/mp4',
            },
            # ExpiresIn=3600  # URL valid for 1 hour
        )
        return presigned_url

    async def generate_presigned_thumbnail_url(self, thumbnail_id: str) -> str:
        presigned_url = self.s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.S3_VIDEO_THUMBNAILS_BUCKET,
                'Key': thumbnail_id,
                # 'ACL': 'private',
                'ContentType': 'image/jpg',
            },
            # ExpiresIn=3600  # URL valid for 1 hour
        )
        return presigned_url

    async def save_video_metadata(
            self,
            user_id: str,
            title: str,
            description: str,
            video_s3_key: str,
            visibility: str,
    ) -> Video:
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
        statement = (
            select(Video)
            .where(Video.id == video_id)
            .limit(1)
        )
        video = self.db.execute(statement).scalar_one_or_none()
        if not video:
            raise ValueError("Video not found")

        video.processing_status = status
        self.db.commit()
