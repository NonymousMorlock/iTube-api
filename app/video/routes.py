from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.core.entities.auth_user import AuthUser
from app.core.middleware.auth_user import get_current_user, verify_iam_auth
from app.video import schemas
from app.video.deps import get_video_service

if TYPE_CHECKING:
    from app.video import VideoService

router = APIRouter(prefix="/videos", tags=["Videos"])


@router.post('/upload-url', response_model=schemas.MediaUploadResponse)
async def get_presigned_video_url(
        current_user: AuthUser = Depends(get_current_user),
        service: "VideoService" = Depends(get_video_service),
):
    return await service.generate_presigned_video_url(current_user)


@router.post('/thumbnail/upload-url', response_model=schemas.MediaUploadResponse)
async def get_presigned_thumbnail_url(
        current_user: AuthUser = Depends(get_current_user),
        service: "VideoService" = Depends(get_video_service),
):
    return await service.generate_presigned_thumbnail_url(current_user)


@router.post('/metadata', response_model=schemas.Video)
async def upload_video_metadata(
        metadata: schemas.VideoBase,
        current_user: AuthUser = Depends(get_current_user),
        service: "VideoService" = Depends(get_video_service),
):
    return await service.save_video_metadata(current_user, metadata)


@router.get('/', response_model=list[schemas.Video])
async def get_all_videos(
        _: AuthUser = Depends(get_current_user),
        service: "VideoService" = Depends(get_video_service),
):
    return await service.get_all_videos()


@router.get('/{video_id}', response_model=schemas.Video)
async def get_video_by_id(
        video_id: str,
        _: AuthUser = Depends(get_current_user),
        service: "VideoService" = Depends(get_video_service),
):
    return await service.get_video_by_id(video_id)


@router.get('/by-key/{s3_key:path}', response_model=schemas.VideoIdResponse)
async def get_video_id_by_s3_key(
        s3_key: str,
        _: str = Depends(verify_iam_auth),
        service: "VideoService" = Depends(get_video_service),
):
    """Get video ID by S3 key. IAM-authenticated endpoint for service-to-service communication."""
    return await service.get_video_id_by_s3_key(s3_key)


@router.patch('/{video_id}/status', response_model=None)
async def update_video_processing_status(
        video_id: str,
        status: str,
        _: str = Depends(verify_iam_auth),
        service: "VideoService" = Depends(get_video_service),
):
    """Update video processing status. IAM-authenticated endpoint for service-to-service communication."""
    return await service.update_video_processing_status(video_id=video_id, status=status)
