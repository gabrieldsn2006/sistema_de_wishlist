from sqlalchemy.orm import Session

import models
import schemas
from security import hash_password


# ---------- Users ----------
def list_users(db: Session):
    return db.query(models.User).all()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, data: schemas.UserCreate):
    values = data.model_dump()
    values["password"] = hash_password(values["password"])
    user = models.User(**values)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, data: schemas.UserUpdate):
    user = get_user(db, user_id)
    if not user:
        return None
    values = data.model_dump(exclude_unset=True)
    if values.get("password"):
        values["password"] = hash_password(values["password"])
        user.session_version += 1  # trocar a senha derruba as sessões abertas
    for field, value in values.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def update_user_role(db: Session, user: models.User, role: str):
    user.role = role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user


# ---------- Games ----------
def list_games(db: Session):
    return db.query(models.Game).all()


def get_game(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.id == game_id).first()


def create_game(db: Session, data: schemas.GameCreate):
    game = models.Game(**data.model_dump())
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def update_game(db: Session, game_id: int, data: schemas.GameUpdate):
    game = get_game(db, game_id)
    if not game:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(game, field, value)
    db.commit()
    db.refresh(game)
    return game


def delete_game(db: Session, game_id: int):
    game = get_game(db, game_id)
    if not game:
        return None
    db.delete(game)
    db.commit()
    return game


# ---------- Wishlist ----------
def list_wishlist_by_user(db: Session, user_id: int):
    return db.query(models.Wishlist).filter(models.Wishlist.user_id == user_id).all()


def get_wishlist_item(db: Session, wishlist_id: int, user_id: int):
    """Só encontra o item se ele pertencer ao usuário informado."""
    return (
        db.query(models.Wishlist)
        .filter(models.Wishlist.id == wishlist_id, models.Wishlist.user_id == user_id)
        .first()
    )


def find_in_wishlist(db: Session, user_id: int, game_id: int):
    return (
        db.query(models.Wishlist)
        .filter(models.Wishlist.user_id == user_id, models.Wishlist.game_id == game_id)
        .first()
    )


def add_to_wishlist(db: Session, user_id: int, data: schemas.WishlistCreate):
    item = models.Wishlist(user_id=user_id, game_id=data.game_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def remove_from_wishlist(db: Session, wishlist_id: int, user_id: int):
    item = get_wishlist_item(db, wishlist_id, user_id)
    if not item:
        return None
    db.delete(item)
    db.commit()
    return item


def game_is_wished(db: Session, game_id: int) -> bool:
    """True se o jogo está na wishlist de alguém (ou seja, precisa continuar monitorado)."""
    return db.query(models.Wishlist.id).filter(models.Wishlist.game_id == game_id).first() is not None


def users_wishing(db: Session, game_id: int) -> list[int]:
    rows = db.query(models.Wishlist.user_id).filter(models.Wishlist.game_id == game_id).distinct().all()
    return [row.user_id for row in rows]


# ---------- Alertas ----------
def create_alerts(db: Session, event: schemas.PriceDropEvent) -> int:
    """Cria um alerta para cada usuário com o jogo na wishlist. Ignora eventos repetidos."""
    created = 0
    for user_id in users_wishing(db, event.game_id):
        exists = (
            db.query(models.Alert.id)
            .filter(models.Alert.user_id == user_id, models.Alert.event_id == event.event_id)
            .first()
        )
        if exists:
            continue
        db.add(models.Alert(
            user_id=user_id,
            game_id=event.game_id,
            event_id=event.event_id,
            old_price=event.old_price,
            new_price=event.new_price,
            normal_price=event.normal_price,
            store=event.store,
            deal_url=event.deal_url,
            currency=event.currency,
        ))
        created += 1
    db.commit()
    return created


def list_alerts(db: Session, user_id: int):
    return (
        db.query(models.Alert)
        .filter(models.Alert.user_id == user_id)
        .order_by(models.Alert.created_at.desc(), models.Alert.id.desc())
        .all()
    )


def delete_alert(db: Session, alert_id: int, user_id: int):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id, models.Alert.user_id == user_id).first()
    if not alert:
        return None
    db.delete(alert)
    db.commit()
    return alert
