"""Entrega dos avisos de queda de preço à Wishlist API, por webhook.

Cada aviso é gravado primeiro na tabela webhook_outbox (padrão "outbox") e só depois
enviado. Se a Wishlist API estiver dormindo ou fora do ar, o aviso fica pendente e
é reenviado no próximo /check. O event_id é sempre o mesmo para o mesmo aviso, e a
Wishlist API ignora repetidos, então reenviar nunca gera alerta duplicado.
"""

import json
import os
from datetime import datetime, timezone

import requests
from sqlalchemy.orm import Session

import models
from signing import sign_headers

WISHLIST_API_URL = os.getenv("WISHLIST_API_URL", "http://localhost:8000").rstrip("/")
WEBHOOK_PATH = "/webhooks/price-drop"
WAKE_TIMEOUT = 90  # no Render free o serviço dormindo leva até ~1 minuto para acordar
SEND_TIMEOUT = 15
MAX_ATTEMPTS = 10


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def enqueue(db: Session, event: dict) -> bool:
    """Grava o aviso no outbox. Devolve False se esse event_id já existia."""
    exists = db.query(models.WebhookOutbox).filter(models.WebhookOutbox.event_id == event["event_id"]).first()
    if exists:
        return False
    db.add(models.WebhookOutbox(event_id=event["event_id"], payload=json.dumps(event), created_at=utcnow()))
    db.commit()
    return True


def _wake_wishlist_api() -> bool:
    try:
        requests.get(f"{WISHLIST_API_URL}/", timeout=WAKE_TIMEOUT)
        return True
    except requests.RequestException:
        return False


def _send(payload: str) -> tuple[bool, str | None]:
    body = payload.encode()
    headers = {"Content-Type": "application/json", **sign_headers("POST", WEBHOOK_PATH, body)}
    try:
        response = requests.post(f"{WISHLIST_API_URL}{WEBHOOK_PATH}", data=body, headers=headers, timeout=SEND_TIMEOUT)
    except requests.RequestException as error:
        return False, f"Falha de conexão: {error.__class__.__name__}"
    if response.ok:
        return True, None
    return False, f"Wishlist API respondeu {response.status_code}: {response.text[:150]}"


def flush(db: Session) -> tuple[int, int, list[str]]:
    """Tenta entregar todos os avisos pendentes. Devolve (entregues, pendentes, erros)."""
    pending = (
        db.query(models.WebhookOutbox)
        .filter(models.WebhookOutbox.delivered_at.is_(None), models.WebhookOutbox.attempts < MAX_ATTEMPTS)
        .order_by(models.WebhookOutbox.id)
        .all()
    )
    if not pending:
        return 0, 0, []

    if not _wake_wishlist_api():
        return 0, len(pending), ["Wishlist API não respondeu; avisos ficam para a próxima rodada"]

    delivered, errors = 0, []
    for item in pending:
        ok, error = _send(item.payload)
        item.attempts += 1
        if ok:
            item.delivered_at = utcnow()
            item.last_error = None
            delivered += 1
        else:
            item.last_error = error[:255]
            errors.append(f"{item.event_id}: {error}")
        db.commit()
        if not ok and error.startswith("Falha de conexão"):
            break  # a Wishlist API caiu no meio: o resto fica para a próxima rodada

    return delivered, len(pending) - delivered, errors
