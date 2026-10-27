from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers
import models
import schemas
from database import get_db
from security import ROLE_ADMIN, get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])


def ensure_self_or_admin(user: models.User, id: int):
    if user.id != id and user.role != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Acesso negado")


# Cadastro: rota pública, sempre cria o papel "user"
@router.post("", response_model=schemas.UserResponse, status_code=201)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if controllers.get_user_by_email(db, user.email):
        raise HTTPException(status_code=409, detail="Email já cadastrado")
    return controllers.create_user(db, user)


@router.get("", response_model=list[schemas.UserResponse])
def list_users(admin: models.User = Depends(require_admin), db: Session = Depends(get_db)):
    return controllers.list_users(db)


@router.get("/{id}", response_model=schemas.UserResponse)
def get_user(id: int, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_self_or_admin(current, id)
    user = controllers.get_user(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return user


# Cada um só edita a própria conta (nem o admin altera senha/email de outra pessoa)
@router.put("/{id}", response_model=schemas.UserResponse)
def update_user(
    id: int,
    user: schemas.UserUpdate,
    current: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current.id != id:
        raise HTTPException(status_code=403, detail="Acesso negado")
    if user.email and user.email != current.email and controllers.get_user_by_email(db, user.email):
        raise HTTPException(status_code=409, detail="Email já cadastrado")
    return controllers.update_user(db, id, user)


@router.patch("/{id}/role", response_model=schemas.UserResponse)
def update_user_role(
    id: int,
    data: schemas.RoleUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if admin.id == id:
        raise HTTPException(status_code=400, detail="Um admin não pode alterar o próprio papel")
    user = controllers.get_user(db, id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return controllers.update_user_role(db, user, data.role)


@router.delete("/{id}", status_code=200)
def delete_user(id: int, current: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_self_or_admin(current, id)
    deleted = controllers.delete_user(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"message": "Usuário deletado com sucesso"}
