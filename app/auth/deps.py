from botocore.client import BaseClient
from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth import AuthRepository
from app.core.cognito import get_cognito_client
from app.core.database import get_db


async def get_auth_repo(cognito: BaseClient = Depends(get_cognito_client), database: Session = Depends(get_db)):
    return AuthRepository(cognito, database)


async def get_auth_service(repo: AuthRepository = Depends(get_auth_repo)):
    from app.auth import AuthService

    return AuthService(repo)
