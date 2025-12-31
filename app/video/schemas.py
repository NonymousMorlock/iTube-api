from uuid import UUID

from pydantic import ConfigDict, BaseModel


class MediaUploadResponse(BaseModel):
    url: str
    media_id: str

    model_config = ConfigDict(from_attributes=True)


class VideoBase(BaseModel):
    title: str
    description: str | None = None
    video_s3_key: str
    visibility: str  # Should be one of "PUBLIC", "PRIVATE", "UNLISTED"

    model_config = ConfigDict(from_attributes=True)


class Video(VideoBase):
    id: UUID | str
    user_id: str
    processing_status: str  # Should be one of "IN_PROGRESS", "COMPLETED", "FAILED"


class VideoIdResponse(BaseModel):
    video_id: str

    model_config = ConfigDict(from_attributes=True)
