# Autenticação e autorização

Requisito do professor: **sem OAuth2 e sem Bearer Token**.

| Peça | Solução |
|---|---|
| Senha | Hash **Argon2** (`pwdlib`). Senhas antigas em texto puro são convertidas no primeiro login. |
| Segundo fator | Código de 6 dígitos por **SMS** (OTP), enviado pelo [Twilio Verify](https://www.twilio.com/docs/verify) (ou, como alternativa, pelo [textbee.dev](https://textbee.dev)). |
| Sessão | **Cookie assinado** (`itsdangerous`) com `{uid, sv, stage}`. Nada fica guardado no servidor, então a API continua **stateless**. |
| Revogação | `session_version` no usuário. Incrementar o número invalida todos os cookies antigos (logout de todos os dispositivos, troca de senha). |
| Autorização | Papéis `admin` e `user` (coluna `role`). |

---

## Fluxo de login

```
POST /auth/login    {email, password}          → 200 + cookie "pendente" + SMS com o código
POST /auth/verify   {code}           + cookie  → 200 + cookie "ativo"
GET  /wishlist                       + cookie  → 200
POST /auth/logout                              → 200 (apaga o cookie)
```

- Com o cookie **pendente**, toda rota protegida responde `401 Verificação pendente`.
- O código vale **5 minutos** e aceita **5 tentativas** (depois, `429`). É de uso único: depois de aceito, é apagado.
- Com o **Twilio Verify**, quem gera e confere o código é o Twilio; a API só guarda a validade e as tentativas. Com o textbee ou no `SMS_DEV_MODE`, a API gera o código e guarda só o hash (`otp_hash`), nunca o texto puro.
- Fazer o login de novo gera um código novo e zera as tentativas.

## Papéis

| Papel | Pode |
|---|---|
| `admin` | Adicionar, editar e remover jogos; listar usuários; alterar o papel de outros usuários |
| `user` | Adicionar, listar e remover jogos da **própria** wishlist |

- Todo cadastro pelo `POST /users` cria um `user`. O corpo não aceita `role`, senão qualquer um viraria admin.
- O primeiro admin é criado no banco:
  ```sql
  UPDATE users SET role = 'admin' WHERE email = 'admin@email.com';
  ```
  Depois disso, um admin promove outros pelo `PATCH /users/{id}/role`. Um admin não pode alterar o próprio papel, para não ficar sem nenhum admin por engano.
- O `user_id` da wishlist vem sempre da sessão. Itens de outros usuários respondem `404`, para não revelar que existem.
- Cada usuário só edita a própria conta (`PUT /users/{id}`). Ver e apagar contas: o próprio usuário ou um admin.

## Respostas de erro

| Situação | Status |
|---|---|
| Sem cookie, cookie adulterado, expirado ou revogado | `401` |
| Sessão pendente (falta o código do SMS) | `401` |
| Código do SMS errado ou expirado | `401` |
| Muitas tentativas de código | `429` |
| Logado, mas sem permissão para a rota | `403` |
| Falha no envio do SMS | `503` |

---

## Configuração

1. `pip install -r requirements.txt`
2. Rodar no banco da Aiven, na ordem e uma vez só:
   - `migrations/001_auth.sql` (`session_version` e `role`)
   - `migrations/002_otp.sql` (campos do código do SMS)
3. Variáveis no `.env` e no Render:
   ```env
   SECRET_KEY=<gerar com: python -c "import secrets; print(secrets.token_hex(32))">
   SMS_PROVIDER=twilio
   TWILIO_ACCOUNT_SID=<Account SID do painel do Twilio>
   TWILIO_AUTH_TOKEN=<Auth Token do painel do Twilio>
   TWILIO_VERIFY_SERVICE_SID=<SID do Verify Service, começa com VA>
   ```
   Só no ambiente local:
   ```env
   COOKIE_SECURE=false   # o cookie Secure não é enviado em http
   SMS_DEV_MODE=true     # o código aparece no log do servidor em vez de ir por SMS
   ```

### Twilio Verify (provedor padrão)

1. Criar uma conta em twilio.com (não pede cartão).
2. No Console, copiar o **Account SID** e o **Auth Token**.
3. Criar um **Verify Service** (Console → Verify → Services, ou pela API) e copiar o SID dele, que começa com `VA`.
4. No trial, o código só chega em números verificados (o número usado no cadastro já é verificado; dá para adicionar até 5) e só no país do cadastro.

Limites do trial (30 dias): **40 verificações grátis**. Uma verificação só é descontada quando o código é confirmado com sucesso. Para o dia a dia, usar `SMS_DEV_MODE=true`.

O trial não aceita SMS com texto personalizado nem dá número próprio, por isso usamos o Verify, que tem mensagem e remetente do próprio Twilio.

A API do Twilio é chamada direto com `requests`, autenticando por HTTP Basic (Account SID + Auth Token), sem SDK.

### textbee (alternativa)

Para usar, trocar para `SMS_PROVIDER=textbee` e definir `TEXTBEE_API_KEY`.

1. Criar uma conta em textbee.dev, instalar o app num Android com chip e conectar pelo QR code.
2. Copiar a API key para `TEXTBEE_API_KEY`.
3. O celular precisa estar ligado e com internet na hora do login (inclusive na apresentação).
4. Plano grátis: 1 celular, 50 SMS por dia e 300 por mês. O SMS sai pelo plano do chip.

### Usuários que já existiam

- Usuários sem telefone não conseguem fazer login (`400`), porque não têm para onde receber o código. Cadastrar o telefone no banco no formato `+5582999999999`.
- Telefones antigos fora desse formato (ex.: `85999991111`) precisam ser corrigidos no banco para o SMS chegar.

---

## Onde está no código

| Arquivo | Conteúdo |
|---|---|
| `src/security.py` | Hash de senha, cookie de sessão, `get_current_user`, `require_admin`, `require_user` |
| `src/sms.py` | Envio e conferência do código pelo Twilio Verify ou textbee (e o modo de desenvolvimento) |
| `src/routers/auth.py` | `/auth/login`, `/auth/verify`, `/auth/logout`, `/auth/logout-all`, `/auth/me` |
| `src/routers/*.py` | Cada rota declara quem pode acessá-la com `Depends(...)` |

Para proteger uma rota nova:

```python
from security import get_current_user, require_admin, require_user

@router.get("/algo")
def algo(user: models.User = Depends(get_current_user)):  # qualquer usuário logado
    ...

@router.post("/algo-de-admin")
def so_admin(user: models.User = Depends(require_admin)):  # sem login → 401; não é admin → 403
    ...
```
