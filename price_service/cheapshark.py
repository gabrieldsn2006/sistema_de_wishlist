"""Cliente da API externa CheapShark (https://apidocs.cheapshark.com/).

TODO (equipe): implementar as funções marcadas com TODO. O resto do Serviço de Preços
(main.py) já usa esta interface, então basta respeitar as assinaturas e os formatos
de retorno descritos em cada função.

Enquanto não estiver implementado, as funções lançam CheapSharkError: o serviço
continua no ar, mas todo jogo aparece como "não encontrado" (found=false).

Regras da CheapShark:
- Grátis e sem chave, mas exige um User-Agent descritivo (com o genérico do
  requests ela responde erro). Use USER_AGENT abaixo.
- Tem limite de requisições: quando passa do limite, responde 429. Nesse caso,
  lance RateLimited, para o /check parar de chamar a API naquela rodada.
- Preços sempre em dólar, como texto ("14.99").
"""

import os

import requests

BASE_URL = "https://www.cheapshark.com/api/1.0"
USER_AGENT = os.getenv("CHEAPSHARK_USER_AGENT", "WishlistAV3/1.0")
TIMEOUT = 15
BATCH_SIZE = 25  # máximo de ids por chamada em /games?ids=


class CheapSharkError(Exception):
    """Qualquer falha ao falar com a CheapShark (rede, status de erro, resposta inesperada)."""


class RateLimited(CheapSharkError):
    """A CheapShark respondeu 429 (excesso de requisições)."""


def search_game(title: str) -> dict | None:
    """Procura um jogo pelo título. Devolve o melhor resultado ou None se não achar nada.

    TODO: implementar com GET {BASE_URL}/games?title=<título>
      - Dica: o parâmetro exact=1 só devolve títulos idênticos. Tente com ele primeiro
        e, se vier vazio, busque sem ele (com limit=10) e prefira o resultado cujo
        "external" for igual ao título, ignorando maiúsculas e pontuação.
      - Precisa do header User-Agent e de timeout=TIMEOUT.
      - 429 → raise RateLimited; outro erro de rede ou status → raise CheapSharkError.

    Formato esperado de retorno (um item da lista que a CheapShark devolve):
        {
            "gameID": "206516",          # obrigatório: id do jogo na CheapShark
            "steamAppID": "1174180",     # pode ser None
            "external": "Red Dead Redemption 2",
            "cheapest": "14.96",
            ...
        }
    """
    raise CheapSharkError("search_game ainda não implementado")


def get_games(cheapshark_ids: list[str]) -> dict[str, dict]:
    """Detalhes de vários jogos de uma vez. A chave do dicionário é o gameID da CheapShark.

    TODO: implementar com GET {BASE_URL}/games?ids=<id1>,<id2>,...
      - A CheapShark aceita no máximo BATCH_SIZE (25) ids por chamada: divida a lista
        em lotes e junte os resultados num dicionário só.
      - Mesmas regras de User-Agent, timeout e erros de search_game.

    Formato esperado de retorno:
        {
            "206516": {
                "info": {"title": "Red Dead Redemption 2", "steamAppID": "1174180"},
                "cheapestPriceEver": {"price": "12.00", "date": 1795280015},
                "deals": [
                    {"storeID": "23", "dealID": "HSOe...", "price": "14.96",
                     "retailPrice": "59.99", "savings": "75.062510"},
                    ...
                ]
            },
            ...
        }
    """
    raise CheapSharkError("get_games ainda não implementado")


def store_name(store_id: str | None) -> str | None:
    """Nome da loja a partir do id (ex.: "1" → "Steam").

    TODO: buscar a lista em GET {BASE_URL}/stores (lista de {"storeID", "storeName", ...})
    e guardar em cache na memória (por exemplo, por um dia), para não chamar a API
    a cada resposta. Se a CheapShark falhar, não lance erro: devolva "Loja <id>".
    """
    if not store_id:
        return None
    return f"Loja {store_id}"


# ---------- Funções que só tratam os dados (já prontas) ----------
def best_deal(game_details: dict) -> dict | None:
    """A oferta mais barata entre as lojas de um item devolvido por get_games."""
    deals = game_details.get("deals") or []
    if not deals:
        return None
    return min(deals, key=lambda deal: float(deal["price"]))


def deal_url(deal_id: str | None) -> str | None:
    """Link que leva o usuário para a oferta na loja (a CheapShark redireciona)."""
    return f"https://www.cheapshark.com/redirect?dealID={deal_id}" if deal_id else None
