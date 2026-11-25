from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TrackRequest(BaseModel):
    game_id: int = Field(gt=0, description="Id do jogo na Wishlist API")
    title: str = Field(min_length=1, max_length=150)


class PriceResponse(BaseModel):
    game_id: int
    title: str
    found: bool = Field(description="false enquanto o jogo não for encontrado na CheapShark")
    cheapshark_id: Optional[str] = None
    steam_app_id: Optional[str] = None
    current_price: Optional[float] = None
    normal_price: Optional[float] = None
    savings_percent: Optional[float] = None
    store: Optional[str] = None
    deal_url: Optional[str] = None
    cheapest_ever: Optional[float] = None
    currency: str = "USD"
    last_checked_at: Optional[datetime] = None


class HistoryEntry(BaseModel):
    price: float
    normal_price: Optional[float] = None
    store: Optional[str] = None
    checked_at: datetime


class CheckResult(BaseModel):
    checked: int = Field(description="Jogos consultados na CheapShark")
    newly_found: int = Field(description="Jogos encontrados na CheapShark pela primeira vez")
    price_drops: int = Field(description="Quedas de preço detectadas nesta rodada")
    delivered: int = Field(description="Avisos entregues à Wishlist API (incluindo os pendentes de rodadas anteriores)")
    pending: int = Field(description="Avisos que continuam pendentes para a próxima rodada")
    errors: list[str] = []
