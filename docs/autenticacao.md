# Autenticação e autorização

Requisito do professor: **sem OAuth2 e sem Bearer Token**.

O projeto tem dois tipos de autenticação:

1. **Usuários** (Streamlit, Postman) → email e senha, com sessão em cookie assinado.
2. **Serviço para serviço** (Wishlist API ↔ Serviço de Preços, GitHub Actions → Serviço de Preços) → assinatura **HMAC** em cada requisição.

---

## 1. Usuários

| Peça | Solução |
|---|---|
| Senha | Hash **Argon2** (`pwdlib`). Senhas antigas em texto puro são convertidas no primeiro login. |
| Sessão | **Cookie assinado** (`itsdangerous`) com `{uid, sv, stage}`. Nada fica guardado no servidor, então a API continua **stateless**. |
| Revogação | `session_version` no usuário. Incrementar o número invalida todos os cookies antigos (logout de todos os dispositivos, troca de senha). |
| Autorização | Papéis `admin` e `user` (coluna `role`). |

Na AV2 o login tinha um segundo fator por SMS (Twilio Verify). Ele saiu na AV3 porque complicava demais o acesso à aplicação (trial com poucos SMS, só para números verificados).

### Fluxo de login

```
POST /auth/login    {email, password}          → 200 + cookie de sessão
GET  /wishlist                       + cookie  → 200
POST /auth/logout                              → 200 (apaga o cookie)
POST /auth/logout-all                + cookie  → 200 (derruba as sessões de todos os dispositivos)
```

A sessão vale 8 horas. O cookie é `HttpOnly`, `SameSite=Lax` e `Secure` (em produção).

### Papéis

| Papel | Pode |
|---|---|
| `admin` | Adicionar, editar e remover jogos; listar usuários; alterar o papel de outros usuários |
| `user` | Adicionar, listar e remover jogos da **própria** wishlist; ver os **próprios** alertas de preço |

- Todo cadastro pelo `POST /users` cria um `user`. O corpo não aceita `role`, senão qualquer um viraria admin.
- O primeiro admin é criado no banco:
  ```sql
  UPDATE users SET role = 'admin' WHERE email = 'admin@email.com';
  ```
  Depois disso, um admin promove outros pelo `PATCH /users/{id}/role`. Um admin não pode alterar o próprio papel, para não ficar sem nenhum admin por engano.
- O `user_id` da wishlist e dos alertas vem sempre da sessão. Itens de outros usuários respondem `404`, para não revelar que existem.
- Cada usuário só edita a própria conta (`PUT /users/{id}`). Ver e apagar contas: o próprio usuário ou um admin.

### Respostas de erro

| Situação | Status |
|---|---|
| Email ou senha errados | `401` |
| Sem cookie, cookie adulterado, expirado ou revogado | `401` |
| Logado, mas sem permissão para a rota | `403` |

---

## 2. Serviço para serviço (HMAC)

As chamadas entre os serviços não têm usuário logado, então a origem é provada por uma **assinatura HMAC-SHA256** com uma chave que só os serviços conhecem (`INTERNAL_SECRET`). Não é Bearer Token: nenhum token é enviado, só a assinatura de cada requisição.

Quem envia calcula:

```
HMAC-SHA256(INTERNAL_SECRET, timestamp + "\n" + MÉTODO + "\n" + caminho?query + "\n" + corpo)
```

e manda nos headers:

```
X-Timestamp: 1764000000
X-Signature: sha256=69f1c8ce...
```

Quem recebe refaz a conta e compara (`hmac.compare_digest`). Isso garante que:

- a requisição veio de quem conhece a chave;
- o corpo, o método e a rota não foram alterados (uma assinatura de `GET /prices/1` não serve para `GET /prices/2`);
- não é uma requisição antiga sendo reenviada: o timestamp precisa estar a no máximo **5 minutos** do relógio do servidor.

Qualquer falha responde `401`.

| Quem chama | Rota | Assinado com |
|---|---|---|
| Wishlist API | `POST /tracked`, `DELETE /tracked/{id}`, `GET /prices...` no Serviço de Preços | `INTERNAL_SECRET` |
| Serviço de Preços | `POST /webhooks/price-drop` na Wishlist API | `INTERNAL_SECRET` |
| GitHub Actions | `POST /check` no Serviço de Preços | `INTERNAL_SECRET` (secret do repositório) |

O código é o mesmo arquivo nos dois serviços: [`src/signing.py`](../src/signing.py) e [`price_service/signing.py`](../price_service/signing.py). Se mudar um, copie para o outro.

---

## Configuração

Variáveis no `.env` e no Render:

```env
SECRET_KEY=<gerar com: python -c "import secrets; print(secrets.token_hex(32))">
INTERNAL_SECRET=<outra chave, gerada do mesmo jeito; igual nos dois serviços e no GitHub Actions>
```

Só no ambiente local:

```env
COOKIE_SECURE=false   # o cookie Secure não é enviado em http
```

---

## Onde está no código

| Arquivo | Conteúdo |
|---|---|
| `src/security.py` | Hash de senha, cookie de sessão, `get_current_user`, `require_admin`, `require_user` |
| `src/signing.py` | Assinatura HMAC das requisições entre os serviços (`sign_headers`, `verify_signature`) |
| `src/routers/auth.py` | `/auth/login`, `/auth/logout`, `/auth/logout-all`, `/auth/me` |
| `src/routers/*.py` | Cada rota declara quem pode acessá-la com `Depends(...)` |

Para proteger uma rota nova:

```python
from security import get_current_user, require_admin, require_user
from signing import verify_signature

@router.get("/algo")
def algo(user: models.User = Depends(get_current_user)):  # qualquer usuário logado
    ...

@router.post("/algo-de-admin")
def so_admin(user: models.User = Depends(require_admin)):  # sem login → 401; não é admin → 403
    ...

@router.post("/rota-interna", dependencies=[Depends(verify_signature)])  # só outro serviço, com HMAC
def interna():
    ...
```
