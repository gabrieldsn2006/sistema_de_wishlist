from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------- Users ----------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    phone: Optional[str] = None
    created_at: Optional[date] = None
    last_update: Optional[date] = None


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
    user_id: int
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
