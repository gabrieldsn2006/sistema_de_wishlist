from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import controllers
import models
import schemas
from database import get_db
from security import require_user
from signing import verify_signature

router = APIRouter(tags=["alertas"])


# ---------- Webhook (chamado pelo Serviço de Preços, não por usuários) ----------
@router.post("/webhooks/price-drop", dependencies=[Depends(verify_signature)])
def price_drop(event: schemas.PriceDropEvent, db: Session = Depends(get_db)):
    """Recebe o aviso de queda de preço e cria um alerta para cada usuário com o jogo na wishlist.

    Exige a assinatura HMAC do Serviço de Preços (headers X-Timestamp e X-Signature).
    Reenviar o mesmo event_id não duplica alertas.
    """
    created = controllers.create_alerts(db, event)
    return {"received": True, "alerts_created": created}


# ---------- Alertas do usuário logado ----------
def to_response(alert: models.Alert) -> schemas.AlertResponse:
    return schemas.AlertResponse(
        id=alert.id,
        game_id=alert.game_id,
        game_title=alert.game.title,
        old_price=alert.old_price,
        new_price=alert.new_price,
        normal_price=alert.normal_price,
        store=alert.store,
        deal_url=alert.deal_url,
        currency=alert.currency,
        created_at=alert.created_at,
    )


@router.get("/alerts", response_model=list[schemas.AlertResponse])
def list_my_alerts(user: models.User = Depends(require_user), db: Session = Depends(get_db)):
    """Quedas de preço dos jogos da wishlist do usuário logado, das mais recentes para as mais antigas."""
    return [to_response(alert) for alert in controllers.list_alerts(db, user.id)]


@router.delete("/alerts/{id}", status_code=200)
def dismiss_alert(id: int, user: models.User = Depends(require_user), db: Session = Depends(get_db)):
    if not controllers.delete_alert(db, id, user.id):
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return {"message": "Alerta removido"}
