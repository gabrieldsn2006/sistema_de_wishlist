from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers
import models
import price_client
import schemas
from database import get_db
from security import require_admin

# Consulta do catálogo é pública; alterar o catálogo é só para admin
router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=schemas.GameResponse, status_code=201)
def create_game(
    game: schemas.GameCreate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return controllers.create_game(db, game)


@router.get("", response_model=list[schemas.GameResponse])
def list_games(db: Session = Depends(get_db)):
    return controllers.list_games(db)


@router.get("/{id}", response_model=schemas.GameResponse)
def get_game(id: int, db: Session = Depends(get_db)):
    game = controllers.get_game(db, id)
    if not game:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return game


@router.put("/{id}", response_model=schemas.GameResponse)
def update_game(
    id: int,
    game: schemas.GameUpdate,
    background: BackgroundTasks,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    current = controllers.get_game(db, id)
    if not current:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    old_title = current.title
    updated = controllers.update_game(db, id, game)
    # Título novo = o Serviço de Preços precisa procurar o jogo de novo na CheapShark
    if updated.title != old_title and controllers.game_is_wished(db, id):
        background.add_task(price_client.track, updated.id, updated.title)
    return updated


@router.delete("/{id}", status_code=200)
def delete_game(
    id: int,
    background: BackgroundTasks,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    deleted = controllers.delete_game(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    background.add_task(price_client.untrack, id)
    return {"message": "Jogo deletado com sucesso"}
