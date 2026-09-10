from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers
import schemas
from database import get_db

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.post("", response_model=schemas.WishlistResponse, status_code=201)
def add_to_wishlist(item: schemas.WishlistCreate, db: Session = Depends(get_db)):
    if not controllers.get_user(db, item.user_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if not controllers.get_game(db, item.game_id):
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return controllers.add_to_wishlist(db, item)


@router.get("/{user_id}", response_model=list[schemas.WishlistResponse])
def list_wishlist(user_id: int, db: Session = Depends(get_db)):
    if not controllers.get_user(db, user_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return controllers.list_wishlist_by_user(db, user_id)


@router.delete("/{id}", status_code=200)
def remove_from_wishlist(id: int, db: Session = Depends(get_db)):
    removed = controllers.remove_from_wishlist(db, id)
    if not removed:
        raise HTTPException(status_code=404, detail="Item da wishlist não encontrado")
    return {"message": "Jogo removido da wishlist com sucesso"}
