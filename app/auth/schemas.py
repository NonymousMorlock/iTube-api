from pydantic import BaseModel, EmailStr, ConfigDict


class EmailSchema(BaseModel):
    email: EmailStr


class UserBase(EmailSchema):
    name: str


class UserCreate(UserBase):
    password: str


#  set orm mode true
class UserRead(UserBase):
    id: str
    name: str
    email: str
    email_verified: bool = False
    cognito_sub: str

    model_config = ConfigDict(from_attributes=True)


class UserLogin(EmailSchema):
    password: str


class EmailVerification(EmailSchema):
    otp: str


class RegistrationSuccess(BaseModel):
    message: str = "User registered successfully. Please check your email to confirm your account."


class AuthTokens(BaseModel):
    access_token: str
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)


class RefreshToken(BaseModel):
    user_cognito_sub: str
    refresh_token: str
