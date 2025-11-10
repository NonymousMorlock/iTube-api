from botocore.client import BaseClient
from fastapi import Depends
from redis import Redis
from sqlalchemy.orm import Session

from app.core.cognito import get_s3_client
from app.core.database import get_db
from app.core.redis import get_redis_client
from app.video import VideoRepository


async def get_video_repo(s3: BaseClient = Depends(get_s3_client), database: Session = Depends(get_db)):
    return VideoRepository(s3, database)


async def get_video_service(
        repo: VideoRepository = Depends(get_video_repo),
        redis_client: Redis = Depends(get_redis_client)
):
    from app.video import VideoService

    return VideoService(video_repo=repo, redis_client=redis_client)
