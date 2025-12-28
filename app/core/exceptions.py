class AppError(Exception):
    """Base app error with optional status code + client message."""

    def __init__(self, message: str, status_code: int | None = 500, detail: str | None = None,
                 error_code: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail or message
        self.error_code = error_code


class NotFoundError(AppError):
    def __init__(self, message="Resource not found"):
        super().__init__(message, status_code=404)


class DomainValidationError(AppError):
    def __init__(self, message="Invalid request data"):
        super().__init__(message, status_code=422)


class UnauthorizedError(AppError):
    def __init__(self, message="Unauthorized access"):
        super().__init__(message, status_code=401)


class ConflictError(AppError):
    def __init__(self, message="Conflict with existing resource"):
        super().__init__(message, status_code=409)


class InternalServerError(AppError):
    def __init__(self, message="Something went wrong", error_code: str | None = None):
        super().__init__(message, status_code=500, error_code=error_code)


class CognitoError(AppError):
    def __init__(self, message='Something went wrong', error_code='Unknown'):
        super().__init__(message=message, error_code=error_code)
