from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Response, Cookie

from app.auth import schemas
from app.auth.deps import get_auth_service
from app.core.entities.auth_user import AuthUser
from app.core.middleware.auth_user import get_current_user

if TYPE_CHECKING:
    from app.auth import AuthService

router = APIRouter(prefix="/auth", tags=['auth'])


@router.post('/signup', response_model=schemas.RegistrationSuccess)
async def register_user(user: schemas.UserCreate, service: "AuthService" = Depends(get_auth_service)):
    return await service.register_user(user)


@router.post('/login', response_model=None)
async def login(credentials: schemas.UserLogin, response: Response, service: "AuthService" = Depends(get_auth_service)):
    tokens = await service.login(credentials)

    response.set_cookie(key='access_token', value=tokens.access_token, httponly=True, secure=True)
    response.set_cookie(key='refresh_token', value=tokens.refresh_token, httponly=True, secure=True)


@router.post('/verify-email', response_model=None)
async def verify_email(payload: schemas.EmailVerification, service: "AuthService" = Depends(get_auth_service)):
    return await service.verify_email(payload)


@router.post('/refresh-token', response_model=None)
async def refresh_user_token(
        response: Response,
        refresh_token: str = Cookie(None),
        user_cognito_sub: str = Cookie(None),
        service: "AuthService" = Depends(get_auth_service)
):
    tokens = await service.refresh_token(
        payload=schemas.RefreshToken(refresh_token=refresh_token, user_cognito_sub=user_cognito_sub)
    )

    response.set_cookie(key="access_token", value=tokens.access_token, httponly=True, secure=True)
    response.set_cookie(key='refresh_token', value=tokens.refresh_token, httponly=True, secure=True)


@router.get('/me', response_model=schemas.UserRead)
async def get_current_user(
        current_user: AuthUser = Depends(get_current_user),
        service: "AuthService" = Depends(get_auth_service),
):
    database_user = await service.get_user_by_cognito_sub(current_user.sub)
    database_user.email_verified = current_user.email_verified
    return database_user
