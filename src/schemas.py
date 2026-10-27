from datetime import date
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Telefone no formato internacional E.164, exigido para o envio do SMS. Ex.: +5582999999999
Phone = Annotated[str, Field(pattern=r"^\+[1-9]\d{7,14}$", examples=["+5582999999999"])]


# ---------- Users ----------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone: Phone


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[Phone] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    phone: Optional[str] = None
    role: str
    created_at: Optional[date] = None
    last_update: Optional[date] = None


# ---------- Auth ----------
class LoginRequest(BaseModel):
    email: str
    password: str


class RoleUpdate(BaseModel):
    role: Literal["admin", "user"]


class VerifyRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$", examples=["123456"])


# ---------- Games ----------
class GameCreate(BaseModel):
    title: str
    genre: Optional[str] = None
    platform: Optional[str] = None
    release_date: Optional[date] = None


class GameUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    platform: Optional[str] = None
    release_date: Optional[date] = None


class GameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    genre: Optional[str] = None
    platform: Optional[str] = None
    release_date: Optional[date] = None
    created_at: Optional[date] = None
    last_update: Optional[date] = None


# ---------- Wishlist ----------
class WishlistCreate(BaseModel):
    game_id: int


class WishlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    game_id: int
    created_at: Optional[date] = None
    last_update: Optional[date] = None


class WishlistDetailResponse(BaseModel):
    """Resposta enriquecida: item da wishlist já com os dados do jogo."""

    id: int
    user_id: int
    game: GameResponse
    created_at: Optional[date] = None
