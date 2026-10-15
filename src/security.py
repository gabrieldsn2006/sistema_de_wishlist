import os
import secrets

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

import models
from database import get_db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("Variável de ambiente SECRET_KEY não definida")

COOKIE_NAME = "session"
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
SESSION_MAX_AGE = 60 * 60 * 8  # 8 horas

# Etapas da sessão guardadas no cookie
STAGE_ACTIVE = "active"
STAGE_PENDING = "pending"  # reservado para o 2FA por SMS (ver docs/autenticacao.md)

password_hash = PasswordHash.recommended()  # Argon2
serializer = URLSafeTimedSerializer(SECRET_KEY, salt="wishlist-session")


# ---------- Senhas ----------
def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(db: Session, user: models.User, password: str) -> bool:
    """Confere a senha. Usuários antigos com senha em texto puro são migrados para Argon2 no login."""
    if not user.password.startswith("$argon2"):
        if not secrets.compare_digest(user.password.encode(), password.encode()):
            return False
        user.password = hash_password(password)
        db.commit()
        return True
    return password_hash.verify(password, user.password)


# ---------- Sessão (cookie assinado, sem estado no servidor) ----------
def set_session_cookie(response: Response, user: models.User, stage: str = STAGE_ACTIVE):
    token = serializer.dumps({"uid": user.id, "sv": user.session_version, "stage": stage})
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )


def clear_session_cookie(response: Response):
    response.delete_cookie(COOKIE_NAME, httponly=True, secure=COOKIE_SECURE, samesite="lax")


def read_session(request: Request, db: Session) -> tuple[models.User, str]:
    """Valida o cookie e devolve (usuário, etapa). Lança 401 se for inválido."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
    except SignatureExpired:
        raise HTTPException(status_code=401, detail="Sessão expirada")
    except BadSignature:
        raise HTTPException(status_code=401, detail="Sessão inválida")

    user = db.query(models.User).filter(models.User.id == data["uid"]).first()
    # session_version diferente = sessão revogada (logout de todos os dispositivos)
    if not user or user.session_version != data["sv"]:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    return user, data["stage"]


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    """Dependência para rotas protegidas: exige sessão ativa."""
    user, stage = read_session(request, db)
    if stage != STAGE_ACTIVE:
        raise HTTPException(status_code=401, detail="Verificação pendente")
    return user


# ---------- Papéis (autorização) ----------
ROLE_ADMIN = "admin"  # gerencia o catálogo de jogos
ROLE_USER = "user"    # monta a própria wishlist


def require_role(*roles: str):
    """Dependência que exige usuário logado com um dos papéis informados (403 caso contrário)."""

    def dependency(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return user

    return dependency


require_admin = require_role(ROLE_ADMIN)
require_user = require_role(ROLE_USER)
