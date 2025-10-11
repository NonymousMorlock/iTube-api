from app.auth import schemas, AuthRepository
from app.core.exceptions import NotFoundError


class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    async def register_user(self, user: schemas.UserCreate) -> schemas.RegistrationSuccess:
        await self.auth_repo.register_user(email=str(user.email), name=user.name, password=user.password)
        return schemas.RegistrationSuccess()

    async def login(self, credentials: schemas.UserLogin) -> schemas.AuthTokens:
        tokens = await self.auth_repo.login(email=str(credentials.email), password=credentials.password)
        return schemas.AuthTokens.model_validate(tokens)

    async def verify_email(self, payload: schemas.EmailVerification) -> None:
        await self.auth_repo.verify_email(email=str(payload.email), otp=payload.otp)
        return None

    async def refresh_token(self, payload: schemas.RefreshToken) -> schemas.AuthTokens:
        tokens = await self.auth_repo.refresh_token(
            user_cognito_sub=payload.user_cognito_sub,
            refresh_token=payload.refresh_token,
        )
        return schemas.AuthTokens.model_validate(tokens)

    async def get_user_by_cognito_sub(self, cognito_sub: str) -> schemas.UserRead:
        user = await self.auth_repo.get_user_by_cognito_sub(cognito_sub)
        if not user:
            raise NotFoundError("User not found")
        return schemas.UserRead.model_validate(user)
