"""Serviço de Preços: monitora os preços dos jogos na CheapShark e avisa a Wishlist API
por webhook quando um preço cai.

Nenhuma rota tem login de usuário: todas (menos GET /) exigem a assinatura HMAC
feita com a chave INTERNAL_SECRET, que só a Wishlist API e o GitHub Actions conhecem.
"""

from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Carrega price_service/.env antes dos outros módulos lerem as variáveis
load_dotenv(Path(__file__).resolve().parent / ".env")

import uvicorn  # noqa: E402
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Response  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import cheapshark  # noqa: E402
import models  # noqa: E402
import notifier  # noqa: E402
import schemas  # noqa: E402
from database import Base, engine, get_db  # noqa: E402
from signing import verify_signature  # noqa: E402

Base.metadata.create_all(bind=engine)

RESOLVE_PER_CHECK = 10  # jogos ainda não encontrados que tentamos achar a cada /check

app = FastAPI(
    title="Serviço de Preços",
    description="Monitora preços na CheapShark e avisa a Wishlist API quando um jogo fica mais barato.",
    version="1.0.0",
)
router = APIRouter(dependencies=[Depends(verify_signature)])


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------- Regras ----------
def resolve(game: models.TrackedGame) -> bool:
    """Procura o jogo na CheapShark pelo título e guarda o gameID dela."""
    found = cheapshark.search_game(game.title)
    if not found:
        return False
    game.cheapshark_id = found["gameID"]
    game.steam_app_id = found.get("steamAppID")
    game.cheapshark_title = found.get("external")
    return True


def apply_details(db: Session, game: models.TrackedGame, details: dict) -> dict | None:
    """Atualiza o preço do jogo. Devolve o aviso de queda de preço, se houver."""
    now = utcnow()
    game.last_checked_at = now
    cheapest = (details.get("cheapestPriceEver") or {}).get("price")
    if cheapest is not None:
        game.cheapest_ever = float(cheapest)

    deal = cheapshark.best_deal(details)
    if not deal:
        return None

    new_price = round(float(deal["price"]), 2)
    normal_price = round(float(deal["retailPrice"]), 2)
    old_price = game.current_price

    if old_price is None or abs(new_price - old_price) >= 0.01:
        db.add(models.PriceHistory(game_id=game.game_id, price=new_price, normal_price=normal_price,
                                   store_id=deal["storeID"], checked_at=now))

    event = None
    if old_price is not None and new_price <= old_price - 0.01:
        event = {
            # Mesmo jogo, loja, preço e dia = mesmo evento (a Wishlist API ignora repetidos)
            "event_id": f"{game.game_id}-{deal['storeID']}-{new_price:.2f}-{now:%Y%m%d}",
            "game_id": game.game_id,
            "title": game.title,
            "old_price": old_price,
            "new_price": new_price,
            "normal_price": normal_price,
            "savings_percent": round(float(deal.get("savings") or 0), 1),
            "store": cheapshark.store_name(deal["storeID"]),
            "deal_url": cheapshark.deal_url(deal.get("dealID")),
            "currency": "USD",
            "detected_at": now.isoformat(),
        }

    game.current_price = new_price
    game.normal_price = normal_price
    game.store_id = deal["storeID"]
    game.deal_id = deal.get("dealID")
    return event


def to_response(game: models.TrackedGame) -> schemas.PriceResponse:
    savings = None
    if game.current_price is not None and game.normal_price:
        savings = round((1 - game.current_price / game.normal_price) * 100, 1)
    return schemas.PriceResponse(
        game_id=game.game_id,
        title=game.title,
        found=game.cheapshark_id is not None,
        cheapshark_id=game.cheapshark_id,
        steam_app_id=game.steam_app_id,
        current_price=game.current_price,
        normal_price=game.normal_price,
        savings_percent=savings,
        store=cheapshark.store_name(game.store_id),
        deal_url=cheapshark.deal_url(game.deal_id),
        cheapest_ever=game.cheapest_ever,
        last_checked_at=game.last_checked_at,
    )


def get_tracked(db: Session, game_id: int) -> models.TrackedGame:
    game = db.get(models.TrackedGame, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Jogo não monitorado")
    return game


# ---------- Rotas ----------
@app.get("/", tags=["status"])
def health():
    """Rota pública, usada para acordar o serviço no Render."""
    return {"message": "Serviço de Preços no ar"}


@router.post("/tracked", response_model=schemas.PriceResponse, status_code=201, tags=["monitoramento"])
def track_game(data: schemas.TrackRequest, response: Response, db: Session = Depends(get_db)):
    """Começa a monitorar um jogo. Chamar de novo para o mesmo jogo não duplica nada."""
    game = db.get(models.TrackedGame, data.game_id)
    if game:
        response.status_code = 200
        if game.title != data.title:  # o admin renomeou o jogo: procura de novo, do zero
            game.title = data.title
            game.cheapshark_id = game.steam_app_id = game.cheapshark_title = None
            game.current_price = game.normal_price = game.cheapest_ever = None
            game.store_id = game.deal_id = None
        if game.cheapshark_id:
            db.commit()
            return to_response(game)
    else:
        game = models.TrackedGame(game_id=data.game_id, title=data.title, created_at=utcnow())
        db.add(game)

    # Busca o preço na hora, para a wishlist já mostrar. Se a CheapShark falhar, o /check tenta de novo.
    try:
        if resolve(game):
            details = cheapshark.get_games([game.cheapshark_id]).get(game.cheapshark_id)
            if details:
                apply_details(db, game, details)
    except cheapshark.CheapSharkError as error:
        print(f"[CheapShark] {error}", flush=True)
    db.commit()
    db.refresh(game)
    return to_response(game)


@router.delete("/tracked/{game_id}", tags=["monitoramento"])
def untrack_game(game_id: int, db: Session = Depends(get_db)):
    game = get_tracked(db, game_id)
    db.delete(game)
    db.commit()
    return {"message": "Jogo deixou de ser monitorado"}


@router.get("/prices", response_model=list[schemas.PriceResponse], tags=["preços"])
def list_prices(
    game_ids: str = Query(..., pattern=r"^\d+(,\d+)*$", description="Ids separados por vírgula, ex.: 1,2,3"),
    db: Session = Depends(get_db),
):
    """Preços de vários jogos de uma vez. Jogos não monitorados ficam de fora da resposta."""
    ids = {int(value) for value in game_ids.split(",")}
    games = db.query(models.TrackedGame).filter(models.TrackedGame.game_id.in_(ids)).all()
    return [to_response(game) for game in games]


@router.get("/prices/{game_id}", response_model=schemas.PriceResponse, tags=["preços"])
def get_price(game_id: int, db: Session = Depends(get_db)):
    return to_response(get_tracked(db, game_id))


@router.get("/prices/{game_id}/history", response_model=list[schemas.HistoryEntry], tags=["preços"])
def get_history(game_id: int, db: Session = Depends(get_db)):
    game = get_tracked(db, game_id)
    return [
        schemas.HistoryEntry(price=h.price, normal_price=h.normal_price,
                             store=cheapshark.store_name(h.store_id), checked_at=h.checked_at)
        for h in game.history
    ]


@router.post("/check", response_model=schemas.CheckResult, tags=["monitoramento"])
def check_prices(db: Session = Depends(get_db)):
    """Consulta a CheapShark para todos os jogos monitorados e avisa a Wishlist API das quedas.

    Chamada de tempos em tempos pelo GitHub Actions (.github/workflows/check-prices.yml).
    """
    errors: list[str] = []
    newly_found = 0

    # 1. Tenta achar na CheapShark os jogos que ainda não foram encontrados
    missing = (
        db.query(models.TrackedGame)
        .filter(models.TrackedGame.cheapshark_id.is_(None))
        .limit(RESOLVE_PER_CHECK)
        .all()
    )
    for game in missing:
        try:
            if resolve(game):
                newly_found += 1
        except cheapshark.CheapSharkError as error:
            errors.append(f"Busca de '{game.title}': {error}")
            if isinstance(error, cheapshark.RateLimited):
                break
    db.commit()

    # 2. Consulta os preços em lote e registra as quedas no outbox
    games = db.query(models.TrackedGame).filter(models.TrackedGame.cheapshark_id.isnot(None)).all()
    checked, drops = 0, 0
    try:
        details = cheapshark.get_games([game.cheapshark_id for game in games]) if games else {}
    except cheapshark.CheapSharkError as error:
        details = {}
        errors.append(f"Consulta de preços: {error}")

    for game in games:
        game_details = details.get(game.cheapshark_id)
        if not game_details:
            continue
        checked += 1
        event = apply_details(db, game, game_details)
        db.commit()
        if event and notifier.enqueue(db, event):
            drops += 1

    # 3. Entrega os avisos (os novos e os que ficaram pendentes de rodadas anteriores)
    delivered, pending, send_errors = notifier.flush(db)
    errors.extend(send_errors)

    return schemas.CheckResult(checked=checked, newly_found=newly_found, price_drops=drops,
                               delivered=delivered, pending=pending, errors=errors)


app.include_router(router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
