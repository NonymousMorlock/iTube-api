import logging
from typing import Any

from botocore.client import BaseClient
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.config import settings
from app.core.exceptions import InternalServerError
from app.core.security import get_secret_hash

COGNITO_CLIENT_ID = settings.COGNITO_CLIENT_ID
COGNITO_CLIENT_SECRET = settings.COGNITO_CLIENT_SECRET

logger = logging.getLogger(__name__)


class AuthRepository:
    def __init__(self, cognito: BaseClient, database: Session):
        self.cognito = cognito
        self.db = database

    async def register_user(self, email: str, password: str, name: str):
        response = self.cognito.sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            Username=email,
            Password=password,
            SecretHash=get_secret_hash(
                username=email,
                client_id=COGNITO_CLIENT_ID,
                client_secret=COGNITO_CLIENT_SECRET,
            ),
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': name}
            ]
        )

        cognito_sub = response.get('UserSub')

        if not cognito_sub:
            logger.error("Cognito sign_up did not return UserSub")
            raise InternalServerError("Failed to register user")

        user = User(name=name, email=email, cognito_sub=cognito_sub)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

    async def login(self, email: str, password: str):
        response = self.cognito.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': get_secret_hash(
                    username=email,
                    client_id=COGNITO_CLIENT_ID,
                    client_secret=COGNITO_CLIENT_SECRET
                )
            }
        )

        return self._get_tokens_from_response(response)

    async def verify_email(self, email: str, otp: str):
        self.cognito.confirm_sign_up(
            ClientId=COGNITO_CLIENT_ID,
            Username=email,
            ConfirmationCode=otp,
            SecretHash=get_secret_hash(
                username=email,
                client_id=COGNITO_CLIENT_ID,
                client_secret=COGNITO_CLIENT_SECRET,
            )
        )

    async def refresh_token(self, user_cognito_sub, refresh_token):
        response = self.cognito.initiate_auth(
            ClientId=COGNITO_CLIENT_ID,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token,
                'SECRET_HASH': get_secret_hash(
                    username=user_cognito_sub,
                    client_id=COGNITO_CLIENT_ID,
                    client_secret=COGNITO_CLIENT_SECRET,
                )
            }
        )

        return self._get_tokens_from_response(response)

    async def get_user_by_cognito_sub(self, cognito_sub: str) -> User | None:
        return self.db.query(User).filter(User.cognito_sub == cognito_sub).first()

    @staticmethod
    def _get_tokens_from_response(response: dict[str, Any]) -> dict[str, Any]:
        auth_result = response.get('AuthenticationResult')
        if not auth_result:
            logger.error("Cognito initiate_auth did not return AuthenticationResult")
            raise InternalServerError("Failed to authenticate user")

        access_token = auth_result.get('AccessToken')
        refresh_token = auth_result.get('RefreshToken')

        if not access_token or not refresh_token:
            logger.error("AuthenticationResult missing tokens")
            raise InternalServerError("Failed to authenticate user")

        return {'access_token': access_token, 'refresh_token': refresh_token}
