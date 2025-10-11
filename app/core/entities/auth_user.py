from dataclasses import dataclass


@dataclass
class AuthUser:
    email: str
    email_verified: bool
    name: str
    sub: str
