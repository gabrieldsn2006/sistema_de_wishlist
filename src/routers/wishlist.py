from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers
import models
import price_client
import schemas
from database import get_db
from security import require_user

# Toda a wishlist é do usuário logado: o user_id vem da sessão, nunca do corpo ou da URL
router = APIRouter(prefix="/wishlist", tags=["wishlist"])


@router.post("", response_model=schemas.WishlistResponse, status_code=201)
def add_to_wishlist(
    item: schemas.WishlistCreate,
    background: BackgroundTasks,
    user: models.User = Depends(require_user),
    db: Session = Depends(get_db),
):
    game = controllers.get_game(db, item.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    if controllers.find_in_wishlist(db, user.id, item.game_id):
        raise HTTPException(status_code=409, detail="Jogo já está na wishlist")
    created = controllers.add_to_wishlist(db, user.id, item)
    # Avisa o Serviço de Preços depois de responder, para não atrasar o usuário
    background.add_task(price_client.track, game.id, game.title)
    return created


@router.get("", response_model=list[schemas.WishlistItemWithPrice])
def list_my_wishlist(
    background: BackgroundTasks,
    user: models.User = Depends(require_user),
    db: Session = Depends(get_db),
):
    """Itens da wishlist, cada um com o preço atual vindo do Serviço de Preços (em dólar)."""
    items = controllers.list_wishlist_by_user(db, user.id)
    prices = price_client.get_prices([item.game_id for item in items])

    result = []
    for item in items:
        data = schemas.WishlistItemWithPrice.model_validate(item, from_attributes=True)
        if prices is None:
            data.price_status = "unavailable"
        elif item.game_id in prices:
            data.price = schemas.PriceInfo(**prices[item.game_id])
        else:
            # O Serviço de Preços não conhece o jogo (estava fora do ar quando foi adicionado): pede de novo
            data.price_status = "not_tracked"
            background.add_task(price_client.track, item.game_id, item.game.title)
        result.append(data)
    return result


@router.get("/{id}", response_model=schemas.WishlistResponse)
def get_wishlist_item(id: int, user: models.User = Depends(require_user), db: Session = Depends(get_db)):
    item = controllers.get_wishlist_item(db, id, user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Item da wishlist não encontrado")
    return item


@router.delete("/{id}", status_code=200)
def remove_from_wishlist(
    id: int,
    background: BackgroundTasks,
    user: models.User = Depends(require_user),
    db: Session = Depends(get_db),
):
    removed = controllers.remove_from_wishlist(db, id, user.id)
    if not removed:
        raise HTTPException(status_code=404, detail="Item da wishlist não encontrado")
    # Ninguém mais quer o jogo: o Serviço de Preços pode parar de monitorar
    if not controllers.game_is_wished(db, removed.game_id):
        background.add_task(price_client.untrack, removed.game_id)
    return {"message": "Jogo removido da wishlist com sucesso"}
