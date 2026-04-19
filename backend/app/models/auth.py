from datetime import datetime
from pydantic import BaseModel


class PermissionRequest(BaseModel):
    jwt_token: str
    permission: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    refresh_token_expires_at: datetime

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool

class RegisterRequest(BaseModel):
    name: str  
    username: str
    password: str

class ChangeNameRequest(BaseModel):
    jwt_token: str
    name: str

class ChangePasswordRequest(BaseModel):
    jwt_token: str
    password_old: str  
    password_new: str
    password_new_repeat: str

class ProviderResponse(BaseModel):
    id: int
    name: str
    display_name: str
    logo_url: str


class LogoutReponse(BaseModel):
    success: bool
    
    
class PermissionResponse(BaseModel):
    user_id: int
    permissions: list[str]
    admin: bool