import boto3
from botocore.client import BaseClient

from app.core.config import settings


def get_cognito_client() -> BaseClient:
    return boto3.client('cognito-idp', region_name=settings.REGION_NAME)


def get_s3_client() -> BaseClient:
    return boto3.client('s3', region_name=settings.REGION_NAME)
