"""Assinatura HMAC das requisições entre a Wishlist API e o Serviço de Preços.

Este arquivo é idêntico em src/signing.py e price_service/signing.py: cada serviço
tem deploy próprio no Render, então um não consegue importar o código do outro.

Quem envia calcula um HMAC-SHA256 com a chave compartilhada INTERNAL_SECRET sobre:

    timestamp + "\\n" + MÉTODO + "\\n" + caminho (com a query string) + "\\n" + corpo

e manda dois headers:

    X-Timestamp: 1764000000
    X-Signature: sha256=<hex>

Quem recebe refaz a conta e compara. Assim ele sabe que a requisição veio de quem
conhece a chave, que o corpo e a rota não foram alterados no caminho e, pelo
timestamp, que não é uma requisição antiga sendo reenviada.
"""

import hashlib
import hmac
import os
import time

from fastapi import HTTPException, Request

MAX_AGE_SECONDS = 300  # 5 minutos de tolerância entre os relógios dos serviços


def _require_secret() -> bytes:
    # Lida na hora do uso: cada serviço carrega o próprio .env antes de atender requisições
    secret = os.getenv("INTERNAL_SECRET", "")
    if not secret:
        raise RuntimeError("Variável de ambiente INTERNAL_SECRET não definida")
    return secret.encode()


def compute_signature(timestamp: str, method: str, path: str, body: bytes) -> str:
    message = f"{timestamp}\n{method.upper()}\n{path}\n".encode() + body
    digest = hmac.new(_require_secret(), message, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def sign_headers(method: str, path: str, body: bytes = b"") -> dict[str, str]:
    """Headers para uma requisição de saída. `path` inclui a query string, se houver."""
    timestamp = str(int(time.time()))
    return {
        "X-Timestamp": timestamp,
        "X-Signature": compute_signature(timestamp, method, path, body),
    }


async def verify_signature(request: Request) -> None:
    """Dependência do FastAPI: recusa com 401 qualquer requisição sem assinatura válida."""
    timestamp = request.headers.get("X-Timestamp", "")
    signature = request.headers.get("X-Signature", "")
    if not timestamp.isdigit() or not signature:
        raise HTTPException(status_code=401, detail="Assinatura ausente")
    if abs(time.time() - int(timestamp)) > MAX_AGE_SECONDS:
        raise HTTPException(status_code=401, detail="Timestamp fora da janela permitida")

    path = request.url.path
    if request.url.query:
        path += f"?{request.url.query}"
    body = await request.body()
    expected = compute_signature(timestamp, request.method, path, body)
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Assinatura inválida")
