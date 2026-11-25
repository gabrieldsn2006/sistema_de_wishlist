from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    phone = Column(String(20))
    role = Column(String(20), nullable=False, default="user", server_default="user")  # "admin" ou "user"
    session_version = Column(Integer, nullable=False, default=0, server_default="0")
    created_at = Column(Date, default=func.current_date())
    last_update = Column(Date, default=func.current_date(), onupdate=func.current_date())

    wishlist_items = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    genre = Column(String(80))
    platform = Column(String(80))
    release_date = Column(Date)
    created_at = Column(Date, default=func.current_date())
    last_update = Column(Date, default=func.current_date(), onupdate=func.current_date())

    wishlist_items = relationship("Wishlist", back_populates="game", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="game", cascade="all, delete-orphan")


class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    created_at = Column(Date, default=func.current_date())
    last_update = Column(Date, default=func.current_date(), onupdate=func.current_date())

    user = relationship("User", back_populates="wishlist_items")
    game = relationship("Game", back_populates="wishlist_items")


class Alert(Base):
    """Aviso de queda de preço, criado quando o Serviço de Preços chama o webhook."""

    __tablename__ = "alerts"
    # O mesmo evento nunca vira dois alertas para a mesma pessoa (o webhook pode ser reenviado)
    __table_args__ = (UniqueConstraint("user_id", "event_id", name="uq_alert_user_event"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    event_id = Column(String(100), nullable=False)
    old_price = Column(Numeric(10, 2, asdecimal=False), nullable=False)
    new_price = Column(Numeric(10, 2, asdecimal=False), nullable=False)
    normal_price = Column(Numeric(10, 2, asdecimal=False))
    store = Column(String(80))
    deal_url = Column(String(300))
    currency = Column(String(3), nullable=False, default="USD")
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="alerts")
    game = relationship("Game", back_populates="alerts")
