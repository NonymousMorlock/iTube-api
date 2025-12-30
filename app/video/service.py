import logging
import uuid

from redis import Redis

from app.core.entities.auth_user import AuthUser
from app.video import VideoRepository, schemas
from app.video.models import ProcessingStatus

logger = logging.getLogger(__name__)


class VideoService:
    def __init__(self, video_repo: VideoRepository, redis_client: Redis):
        self.video_repo = video_repo
        self.redis = redis_client

    async def generate_presigned_video_url(self, user: AuthUser) -> schemas.MediaUploadResponse:
        video_id = f'videos/{user.sub}/{uuid.uuid4()}'
        url = await self.video_repo.generate_presigned_video_url(video_id)

        return schemas.MediaUploadResponse(url=url, media_id=video_id)

    async def generate_presigned_thumbnail_url(self, thumbnail_id: str) -> schemas.MediaUploadResponse:
        thumbnail_id = thumbnail_id.replace('videos/', 'thumbnails/')
        url = await self.video_repo.generate_presigned_thumbnail_url(thumbnail_id)

        return schemas.MediaUploadResponse(url=url, media_id=thumbnail_id)

    async def save_video_metadata(self, user: AuthUser, metadata: schemas.VideoBase) -> schemas.Video:
        if metadata.visibility.lower() not in {"public", "private", "unlisted"}:
            raise ValueError("Invalid visibility value")

        video = await self.video_repo.save_video_metadata(
            user_id=user.sub,
            title=metadata.title,
            description=metadata.description,
            video_s3_key=metadata.video_s3_key,
            visibility=metadata.visibility.upper(),
        )
        return schemas.Video.model_validate(video)

    async def get_all_videos(self) -> list[schemas.Video]:
        videos = await self.video_repo.get_all_videos()
        return [schemas.Video.model_validate(video) for video in videos]

    async def get_video_by_id(self, video_id: str) -> schemas.Video:
        cache_key = f'video:{video_id}'

        try:
            cached_video = await self.redis.get(cache_key)
            if cached_video:
                return schemas.Video.model_validate_json(cached_video)
        except Exception as e:
            logger.error(f"Redis error: {e}")

        video = await self.video_repo.get_video_by_id(video_id)

        if not video:
            raise ValueError("Video not found")

        schema_video = schemas.Video.model_validate(video)

        try:
            await self.redis.set(
                cache_key,
                schema_video.model_dump_json(),
                ex=3600
            )
        except Exception as e:
            logger.error(f"Redis error: {e}")

        return schema_video

    async def get_video_id_by_s3_key(self, s3_key: str) -> schemas.VideoIdResponse:
        video = await self.video_repo.get_video_by_s3_key(s3_key)
        if not video:
            raise ValueError("Video not found")
        return schemas.VideoIdResponse(video_id=str(video.id))

    async def update_video_processing_status(self, video_id: str, status: str) -> None:
        if status.lower() not in {'in_progress', 'completed', 'failed'}:
            raise ValueError('Invalid processing status')

        await self.video_repo.update_video_processing_status(video_id=video_id, status=ProcessingStatus[status.upper()])
