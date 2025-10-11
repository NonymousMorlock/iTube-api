from botocore.client import BaseClient
from fastapi import Cookie, Depends

from app.core.cognito import get_cognito_client
from app.core.entities.auth_user import AuthUser
from app.core.exceptions import UnauthorizedError


def _get_cognito_user(access_token: str, cognito_client: BaseClient) -> AuthUser:
    raw_user = cognito_client.get_user(AccessToken=access_token)
    user = {attribute['Name']: attribute['Value'] for attribute in raw_user['UserAttributes']}
    return AuthUser(
        name=user['name'],
        email=user['email'],
        email_verified=user['email_verified'].lower() == 'true',
        sub=user['sub']
    )


def get_current_user(
        access_token: str = Cookie(None),
        cognito_client: BaseClient = Depends(get_cognito_client),
) -> AuthUser:
    if not access_token:
        raise UnauthorizedError('User is not authenticated')

    return _get_cognito_user(access_token=access_token, cognito_client=cognito_client)
