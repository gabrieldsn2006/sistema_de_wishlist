from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

import controllers
import models
import schemas
from database import get_db
from security import clear_session_cookie, get_current_user, set_session_cookie, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", status_code=200)
def login(credentials: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = controllers.get_user_by_email(db, credentials.email)
    if not user or not verify_password(db, user, credentials.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    # TODO (Parte 2 - 2FA por SMS): em vez de criar a sessão ativa aqui,
    # enviar o código por SMS e criar a sessão com stage=STAGE_PENDING.
    set_session_cookie(response, user)
    return {"message": "Login realizado com sucesso"}


@router.post("/logout", status_code=200)
def logout(response: Response):
    clear_session_cookie(response)
    return {"message": "Logout realizado"}


@router.post("/logout-all", status_code=200)
def logout_all(response: Response, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Invalida as sessões do usuário em todos os dispositivos."""
    user.session_version += 1
    db.commit()
    clear_session_cookie(response)
    return {"message": "Todas as sessões foram encerradas"}


@router.get("/me", response_model=schemas.UserResponse)
def me(user: models.User = Depends(get_current_user)):
    return user
