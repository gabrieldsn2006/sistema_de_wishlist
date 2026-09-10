from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers
import schemas
from database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return controllers.create_user(db, user)


@router.get("", response_model=list[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    return controllers.list_users(db)


@router.get("/{id}", response_model=schemas.UserResponse)
def get_user(id: int, db: Session = Depends(get_db)):
    user = controllers.get_user(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


@router.put("/{id}", response_model=schemas.UserResponse)
def update_user(id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    updated = controllers.update_user(db, id, user)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return updated


@router.delete("/{id}", status_code=200)
def delete_user(id: int, db: Session = Depends(get_db)):
    deleted = controllers.delete_user(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"message": "Usuário deletado com sucesso"}
