from sqlalchemy import Column, Date, ForeignKey, Integer, String
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
    created_at = Column(Date, server_default=func.current_date())
    last_update = Column(Date, server_default=func.current_date(), onupdate=func.current_date())

    wishlist_items = relationship("Wishlist", back_populates="user", cascade="all, delete-orphan")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(150), nullable=False)
    genre = Column(String(80))
    platform = Column(String(80))
    release_date = Column(Date)
    created_at = Column(Date, server_default=func.current_date())
    last_update = Column(Date, server_default=func.current_date(), onupdate=func.current_date())

    wishlist_items = relationship("Wishlist", back_populates="game", cascade="all, delete-orphan")


class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    created_at = Column(Date, server_default=func.current_date())
    last_update = Column(Date, server_default=func.current_date(), onupdate=func.current_date())

    user = relationship("User", back_populates="wishlist_items")
    game = relationship("Game", back_populates="wishlist_items")
