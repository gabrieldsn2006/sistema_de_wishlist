from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers
import schemas
from database import get_db

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=schemas.GameResponse, status_code=201)
def create_game(game: schemas.GameCreate, db: Session = Depends(get_db)):
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
def update_game(id: int, game: schemas.GameUpdate, db: Session = Depends(get_db)):
    updated = controllers.update_game(db, id, game)
    if not updated:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return updated


@router.delete("/{id}", status_code=200)
def delete_game(id: int, db: Session = Depends(get_db)):
    deleted = controllers.delete_game(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Jogo não encontrado")
    return {"message": "Jogo deletado com sucesso"}
