# Autenticação — divisão do trabalho

Requisito do professor: **sem OAuth2 e sem Bearer Token**.

Solução escolhida:

- **Senha com hash Argon2** (`pwdlib`).
- **Sessão em cookie assinado** (`itsdangerous`) — a API continua **stateless**: nada de sessão guardada no servidor, o cookie carrega `{uid, sv, stage}` assinado com a `SECRET_KEY`.
- **2FA por SMS** com código de uso único (OTP), enviado por um celular Android via [textbee.dev](https://textbee.dev) (grátis, usa o chip do celular).
- **`session_version`** no usuário: incrementar esse número invalida todos os cookies antigos (logout de todos os dispositivos, troca de senha).
- **Dois papéis** (coluna `role` em `users`):

  | Papel | Pode |
  |---|---|
  | `admin` | Adicionar, editar e remover jogos do catálogo |
  | `user` | Adicionar e remover jogos da própria wishlist |

  Todo cadastro pelo `POST /users` nasce como `user` (o campo `role` não é aceito no corpo, senão qualquer um viraria admin). Para criar um admin, rodar no banco:
  ```sql
  UPDATE users SET role = 'admin' WHERE email = 'admin@email.com';
  ```

---

## Parte 1 — Base da autenticação ✅ (feita)

- `src/security.py`: hash/verificação de senha, criação e leitura do cookie, dependências `get_current_user`, `require_admin` e `require_user`.
- `src/routers/auth.py`: `POST /auth/login`, `POST /auth/logout`, `POST /auth/logout-all`, `GET /auth/me`.
- `controllers.create_user` / `update_user` gravam a senha com hash. Usuários antigos com senha em texto puro são migrados para Argon2 automaticamente no primeiro login.
- `migrations/001_auth.sql`: colunas `session_version` e `role` em `users`.

### Configuração necessária (todos)

1. `pip install -r requirements.txt`
2. Rodar `migrations/001_auth.sql` no banco da Aiven (uma vez só).
3. No `.env` (e nas variáveis do Render):
   ```env
   SECRET_KEY=<gerar com: python -c "import secrets; print(secrets.token_hex(32))">
   COOKIE_SECURE=false   # só no ambiente local (http). No Render deixar true ou omitir.
   ```

### Como usar nas rotas

```python
import models
from security import get_current_user

@router.get("/algo")
def algo(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    ...  # user é o usuário logado; sem sessão ativa a rota já responde 401


from security import require_admin, require_user

@router.post("/algo-de-admin")
def so_admin(user: models.User = Depends(require_admin)):
    ...  # sem login → 401; logado mas não é admin → 403
```

---

## Parte 2 — 2FA por SMS (textbee)

Objetivo: depois de acertar a senha, o usuário recebe um código por SMS e só fica logado depois de digitá-lo.

### Tarefas

1. **Banco** — criar `migrations/002_otp.sql` e os campos no model `User`:
   - `otp_hash` (String 255, nullable) — hash do código, nunca o código puro.
   - `otp_expires_at` (DateTime, nullable) — validade de 5 minutos.
   - `otp_attempts` (Integer, default 0) — máximo de 5 tentativas.
2. **`src/sms.py`** — função `send_sms(phone, message)`:
   ```python
   requests.post(
       "https://api.textbee.dev/api/v1/gateway/send-sms",
       headers={"x-api-key": TEXTBEE_API_KEY},
       json={"recipients": [phone], "message": message},
   )
   ```
   Com `SMS_DEV_MODE=true` no `.env`, só imprimir o código no log em vez de enviar (para não depender do celular nos testes). Adicionar `requests` ao `requirements.txt`.
3. **`POST /auth/login`** (tem um `TODO` marcando o lugar):
   - Gerar o código: `f"{secrets.randbelow(10**6):06d}"`.
   - Salvar `otp_hash` (pode usar `hash_password` do `security.py`), `otp_expires_at` e zerar `otp_attempts`.
   - Enviar o SMS e responder com o telefone mascarado (`+55*******9999`).
   - Criar o cookie como pendente: `set_session_cookie(response, user, STAGE_PENDING)`.
4. **`POST /auth/verify`** — body `{"code": "123456"}`:
   - `user, stage = read_session(request, db)` e exigir `stage == STAGE_PENDING`.
   - Validar expiração (401), tentativas (429) e o código (401, incrementando `otp_attempts`).
   - Se der certo: limpar os campos de OTP e `set_session_cookie(response, user)` (sessão ativa).
5. **Telefone** — validar no `schemas.py` o formato E.164 (`+5582999999999`) e decidir o que fazer com usuário sem telefone (sugestão: tornar `phone` obrigatório no cadastro).

### Configuração do textbee

1. Criar conta em textbee.dev, instalar o app num Android com chip e conectar pelo QR code.
2. Copiar a API key para `TEXTBEE_API_KEY` no `.env` e no Render.
3. O celular precisa estar ligado e com internet na hora do login (inclusive na apresentação).

---

## Parte 3 — Proteger as rotas existentes

Objetivo: aplicar os papéis nas rotas e garantir que cada usuário só mexa nos próprios dados.

### Tarefas

1. **Wishlist** (`routers/wishlist.py`, `controllers.py`, `schemas.py`) — rotas com `Depends(require_user)`:
   - Tirar `user_id` do `WishlistCreate` — ele vem do usuário logado.
   - Trocar `GET /wishlist/by-user/{id}` por `GET /wishlist` (wishlist do usuário logado).
   - `GET /wishlist/{id}` e `DELETE /wishlist/{id}`: se o item não for do usuário logado, responder 404.
2. **Users** (`routers/users.py`):
   - `POST /users` continua público (é o cadastro).
   - `PUT` e `DELETE /users/{id}`: só se `id == user.id`, senão 403.
   - `GET /users` e `GET /users/{id}`: exigir login.
3. **Games** (`routers/games.py`): `GET` público; `POST`, `PUT` e `DELETE` com `Depends(require_admin)`.
4. **(Opcional)** `PATCH /users/{id}/role` só para admin, para promover usuários sem precisar de SQL.
5. **README**: atualizar a tabela de endpoints, os exemplos de requisição (sem `user_id` na wishlist) e adicionar a seção de autenticação com os papéis e o fluxo login → verify → uso → logout.

---

## Fluxo final (depois das 3 partes)

```
POST /users          {username, email, password, phone}   → 201
POST /auth/login     {email, password}                    → 200 + cookie (pendente) + SMS
POST /auth/verify    {code}                     + cookie  → 200 + cookie (ativo)
GET  /wishlist                                  + cookie  → 200
POST /auth/logout                                         → 200 (apaga o cookie)
```
