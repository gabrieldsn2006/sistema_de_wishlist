"""Cliente HTTP do Serviço de Preços (integração REST entre os dois sistemas próprios).

Toda requisição sai assinada com HMAC (ver signing.py). Nenhuma falha aqui derruba a
wishlist: se o Serviço de Preços estiver fora do ar, as funções devolvem None e a
wishlist mostra o preço como indisponível.
"""

import json
import os

import requests

from signing import sign_headers

PRICE_SERVICE_URL = os.getenv("PRICE_SERVICE_URL", "http://localhost:8001").rstrip("/")
# No Render free o Serviço de Preços dorme; a primeira chamada pode estourar o tempo e só acordá-lo
TIMEOUT = float(os.getenv("PRICE_SERVICE_TIMEOUT", "10"))


class PriceServiceUnavailable(Exception):
    pass


def _request(method: str, path: str, payload: dict | None = None) -> requests.Response:
    body = json.dumps(payload).encode() if payload is not None else b""
    headers = sign_headers(method, path, body)
    if payload is not None:
        headers["Content-Type"] = "application/json"
    try:
        return requests.request(method, f"{PRICE_SERVICE_URL}{path}", data=body or None,
                                headers=headers, timeout=TIMEOUT)
    except requests.RequestException as error:
        raise PriceServiceUnavailable(str(error)) from error


def track(game_id: int, title: str) -> bool:
    """Pede para o Serviço de Preços começar a monitorar o jogo."""
    try:
        response = _request("POST", "/tracked", {"game_id": game_id, "title": title})
    except PriceServiceUnavailable as error:
        print(f"[Preços] Não foi possível monitorar o jogo {game_id}: {error}", flush=True)
        return False
    if not response.ok:
        print(f"[Preços] /tracked respondeu {response.status_code}: {response.text[:200]}", flush=True)
    return response.ok


def untrack(game_id: int) -> bool:
    try:
        response = _request("DELETE", f"/tracked/{game_id}")
    except PriceServiceUnavailable as error:
        print(f"[Preços] Não foi possível parar de monitorar o jogo {game_id}: {error}", flush=True)
        return False
    return response.ok or response.status_code == 404


def get_prices(game_ids: list[int]) -> dict[int, dict] | None:
    """Preços de vários jogos numa chamada só. None = Serviço de Preços indisponível.

    Jogos que não estão no dicionário devolvido ainda não são monitorados.
    """
    if not game_ids:
        return {}
    ids = ",".join(str(game_id) for game_id in sorted(set(game_ids)))
    try:
        response = _request("GET", f"/prices?game_ids={ids}")
    except PriceServiceUnavailable:
        return None
    if not response.ok:
        print(f"[Preços] /prices respondeu {response.status_code}: {response.text[:200]}", flush=True)
        return None
    return {item["game_id"]: item for item in response.json()}
