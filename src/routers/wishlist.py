from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers
import models
import schemas
from database import get_db
from security import require_user

# Toda a wishlist é do usuário logado: o user_id vem da sessão, nunca do corpo ou da URL
router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.post("", response_model=schemas.WishlistResponse, status_code=201)
def add_to_wishlist(
    item: schemas.WishlistCreate,
    user: models.User = Depends(require_user),
    db: Session = Depends(get_db),
):
    if not controllers.get_game(db, item.game_id):
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    if controllers.find_in_wishlist(db, user.id, item.game_id):
        raise HTTPException(status_code=409, detail="Jogo já está na wishlist")
    return controllers.add_to_wishlist(db, user.id, item)


@router.get("", response_model=list[schemas.WishlistResponse])
def list_my_wishlist(user: models.User = Depends(require_user), db: Session = Depends(get_db)):
    return controllers.list_wishlist_by_user(db, user.id)


@router.get("/{id}", response_model=schemas.WishlistResponse)
def get_wishlist_item(id: int, user: models.User = Depends(require_user), db: Session = Depends(get_db)):
    item = controllers.get_wishlist_item(db, id, user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Item da wishlist não encontrado")
    return item


@router.delete("/{id}", status_code=200)
def remove_from_wishlist(id: int, user: models.User = Depends(require_user), db: Session = Depends(get_db)):
    removed = controllers.remove_from_wishlist(db, id, user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="Item da wishlist não encontrado")
    return {"message": "Jogo removido da wishlist com sucesso"}
