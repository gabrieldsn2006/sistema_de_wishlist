from datetime import date, datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Telefone opcional, no formato internacional E.164. Ex.: +5582999999999
Phone = Annotated[str, Field(pattern=r"^\+[1-9]\d{7,14}$", examples=["+5582999999999"])]


# ---------- Users ----------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    phone: Optional[Phone] = None


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


class PriceInfo(BaseModel):
    """Preço vindo do Serviço de Preços (sempre em dólar)."""

    found: bool
    current_price: Optional[float] = None
    normal_price: Optional[float] = None
    savings_percent: Optional[float] = None
    store: Optional[str] = None
    deal_url: Optional[str] = None
    cheapest_ever: Optional[float] = None
    currency: str = "USD"
    last_checked_at: Optional[datetime] = None


class WishlistItemWithPrice(WishlistResponse):
    price: Optional[PriceInfo] = None
    price_status: Literal["ok", "not_tracked", "unavailable"] = Field(
        "ok",
        description="ok: preço abaixo; not_tracked: ainda sendo monitorado pela primeira vez; "
        "unavailable: Serviço de Preços fora do ar",
    )


class WishlistDetailResponse(BaseModel):
    """Resposta enriquecida: item da wishlist já com os dados do jogo."""

    id: int
    user_id: int
    game: GameResponse
    created_at: Optional[date] = None


# ---------- Alertas (webhook do Serviço de Preços) ----------
class PriceDropEvent(BaseModel):
    """Corpo do webhook POST /webhooks/price-drop, enviado pelo Serviço de Preços."""

    event_id: str = Field(min_length=1, max_length=100)
    game_id: int
    title: str
    old_price: float
    new_price: float
    normal_price: Optional[float] = None
    savings_percent: Optional[float] = None
    store: Optional[str] = None
    deal_url: Optional[str] = Field(None, max_length=300)
    currency: str = "USD"
    detected_at: Optional[datetime] = None


class AlertResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    game_id: int
    game_title: str
    old_price: float
    new_price: float
    normal_price: Optional[float] = None
    store: Optional[str] = None
    deal_url: Optional[str] = None
    currency: str
    created_at: datetime
