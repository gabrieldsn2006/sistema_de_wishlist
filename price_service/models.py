from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from database import Base

Money = Numeric(10, 2, asdecimal=False)  # preços em dólar, devolvidos como float


class TrackedGame(Base):
    """Jogo monitorado. O id é o mesmo id do jogo na Wishlist API."""

    __tablename__ = "tracked_games"

    game_id = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(String(150), nullable=False)
    cheapshark_id = Column(String(20))  # vazio enquanto o jogo não for encontrado na CheapShark
    steam_app_id = Column(String(20))
    cheapshark_title = Column(String(200))
    current_price = Column(Money)
    normal_price = Column(Money)
    store_id = Column(String(10))
    deal_id = Column(String(200))
    cheapest_ever = Column(Money)
    last_checked_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False)

    history = relationship(
        "PriceHistory",
        back_populates="game",
        cascade="all, delete-orphan",
        order_by="PriceHistory.checked_at",
    )


class PriceHistory(Base):
    """Um registro por mudança de preço (e o primeiro preço encontrado)."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("tracked_games.game_id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Money, nullable=False)
    normal_price = Column(Money)
    store_id = Column(String(10))
    checked_at = Column(DateTime, nullable=False)

    game = relationship("TrackedGame", back_populates="history")


class WebhookOutbox(Base):
    """Avisos de queda de preço a entregar à Wishlist API.

    Todo aviso é gravado aqui antes do envio. Se a Wishlist API estiver fora do ar,
    ele fica pendente e é reenviado no próximo /check.
    """

    __tablename__ = "webhook_outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(100), nullable=False, unique=True)
    payload = Column(Text, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    last_error = Column(String(255))
    created_at = Column(DateTime, nullable=False)
    delivered_at = Column(DateTime)
