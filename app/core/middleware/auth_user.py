import logging
from typing import Optional

from botocore.client import BaseClient
from fastapi import Cookie, Depends, Header, HTTPException, status

from app.core.cognito import get_cognito_client
from app.core.entities.auth_user import AuthUser
from app.core.exceptions import UnauthorizedError

logger = logging.getLogger(__name__)


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


def verify_iam_auth(
        authorization: Optional[str] = Header(None),
        x_amz_date: Optional[str] = Header(None, alias="X-Amz-Date"),
        x_amzn_request_id: Optional[str] = Header(None, alias="X-Amzn-RequestId"),
        x_amz_security_token: Optional[str] = Header(None, alias="X-Amz-Security-Token"),
) -> str:
    """Verify AWS IAM authentication for service-to-service calls.

    This dependency validates IAM-authenticated requests. When used with API Gateway,
    the gateway performs full SigV4 verification before the request reaches this code.
    We verify the request has proper authentication headers and log the principal.

    Args:
        authorization: AWS SigV4 Authorization header
        x_amz_date: Request timestamp (required for SigV4)
        x_amzn_request_id: API Gateway request ID (indicates request came through gateway)
        x_amz_security_token: Session token for temporary credentials (ECS task role)
                             Note: Present in headers but not used in validation logic
                             as API Gateway verifies it. Kept for documentation.

    For API Gateway setup:
    - API Gateway handles signature verification (cryptographic validation)
    - This function validates presence of required headers
    - Logs authenticated requests for audit

    Returns:
        The IAM principal identifier extracted from the authorization header.

    Raises:
        HTTPException: If authentication fails or required headers are missing.
    """
    # x_amz_security_token is intentionally unused in logic but required for
    # complete AWS SigV4 authentication with temporary credentials (ECS task roles).
    # API Gateway validates it; we just document its presence.
    _ = x_amz_security_token
    # Check for API Gateway request ID (indicates request came through API Gateway)
    # If present, API Gateway has already verified the signature
    if x_amzn_request_id:
        logger.info("Request authenticated via API Gateway (request_id=%s)", x_amzn_request_id)
        # API Gateway has verified the signature, extract identity for logging
        if authorization:
            try:
                credential_part = authorization.split("Credential=")[1].split(",")[0]
                access_key = credential_part.split("/")[0]
                logger.info("IAM authenticated request from access key: %s...", access_key[:8])
                return access_key
            except (IndexError, AttributeError):
                # If we can't parse, still allow since API Gateway verified
                logger.info("API Gateway verified request, principal parsing failed (still valid)")
                return "api-gateway-verified"
        return "api-gateway-verified"

    # Direct call (not through API Gateway) - validate headers present
    if not authorization:
        logger.warning("IAM auth failed: Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing AWS Signature authentication headers"
        )

    if not x_amz_date:
        logger.warning("IAM auth failed: Missing X-Amz-Date header")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing X-Amz-Date header"
        )

    # Validate that the authorization header follows AWS Signature V4 format
    if not authorization.startswith("AWS4-HMAC-SHA256"):
        logger.warning("IAM auth failed: Invalid authorization format")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid AWS Signature format"
        )

    # Extract credential information from the Authorization header
    # Format: AWS4-HMAC-SHA256 Credential=AKIAIOSFODNN7EXAMPLE/20130524/us-east-1/s3/aws4_request...
    try:
        credential_part = authorization.split("Credential=")[1].split(",")[0]
        access_key = credential_part.split("/")[0]
        logger.info("IAM authenticated request from access key: %s...", access_key[:8])
        return access_key
    except (IndexError, AttributeError) as e:
        logger.error("Failed to parse AWS authorization header: %s", e)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid AWS Signature format"
        )
