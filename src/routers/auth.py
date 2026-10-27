from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

import controllers
import models
import schemas
import sms
from database import get_db
from security import (
    STAGE_PENDING,
    clear_session_cookie,
    get_current_user,
    hash_password,
    password_hash,
    read_session,
    set_session_cookie,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_VALIDITY = timedelta(minutes=5)
OTP_MAX_ATTEMPTS = 5


def utcnow() -> datetime:
    # O MySQL guarda DATETIME sem fuso, então trabalhamos com UTC "ingênuo"
    return datetime.now(timezone.utc).replace(tzinfo=None)


def mask_phone(phone: str) -> str:
    return phone[:3] + "*" * (len(phone) - 7) + phone[-4:]


@router.post("/login", status_code=200)
def login(credentials: schemas.LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = controllers.get_user_by_email(db, credentials.email)
    if not user or not verify_password(db, user, credentials.password):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not user.phone:
        raise HTTPException(status_code=400, detail="Usuário sem telefone cadastrado para o envio do código")

    try:
        code = sms.send_code(user.phone)
    except sms.SMSError as error:
        print(f"[SMS] {error}", flush=True)  # o motivo fica só no log, não vai para o cliente
        raise HTTPException(status_code=503, detail="Não foi possível enviar o SMS, tente novamente")

    # Com o Twilio Verify o código fica no Twilio; nos outros casos guardamos só o hash
    user.otp_hash = hash_password(code) if code else None
    user.otp_expires_at = utcnow() + OTP_VALIDITY
    user.otp_attempts = 0
    db.commit()

    set_session_cookie(response, user, STAGE_PENDING)
    return {"message": f"Código enviado para {mask_phone(user.phone)}"}


@router.post("/verify", status_code=200)
def verify(data: schemas.VerifyRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user, stage = read_session(request, db)
    if stage != STAGE_PENDING or not user.otp_expires_at:
        raise HTTPException(status_code=400, detail="Nenhuma verificação pendente, faça o login novamente")
    if utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=401, detail="Código expirado, faça o login novamente")
    if user.otp_attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Muitas tentativas, faça o login novamente")

    try:
        if user.otp_hash:
            valid = password_hash.verify(data.code, user.otp_hash)
        else:
            valid = sms.check_code(user.phone, data.code)
    except sms.SMSError as error:
        print(f"[SMS] {error}", flush=True)
        raise HTTPException(status_code=503, detail="Não foi possível conferir o código, tente novamente")

    if not valid:
        user.otp_attempts += 1
        db.commit()
        raise HTTPException(status_code=401, detail="Código inválido")

    # Código de uso único: depois de aceito, não serve mais
    user.otp_hash = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.commit()

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
