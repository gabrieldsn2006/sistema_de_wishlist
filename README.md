# Sistema de Wishlist de Jogos

## Equipe

- Victor Lins Gurgel do Amaral
- Lorenzo Barros Calheiros Pinheiro
- Gabriel De Sousa Nobre

## Descrição do Projeto

Uma wishlist de jogos que **monitora os preços automaticamente e avisa quando um jogo da lista entra em promoção**.

O usuário cria uma conta, monta a lista de jogos que quer comprar e vê o preço atual de cada um (a loja mais barata, o desconto e o menor preço histórico). De tempos em tempos, o sistema consulta os preços em várias lojas de PC pela API da CheapShark. Quando um preço cai, o usuário recebe um alerta.

Projeto da AV3 de Técnicas de Integração de Sistemas: dois sistemas próprios integrados entre si e com uma API externa, com autenticação e deploy.

---

## Arquitetura

```
                ┌──────────────────┐
                │  Streamlit (UI)  │
                └────────┬─────────┘
                         │ REST/JSON + cookie de sessão
                         ▼
┌────────────────────────────────────────┐   REST/JSON assinado (HMAC)
│        Wishlist API (FastAPI)          │ ─────────────────────────────┐
│  auth · users · games · wishlist       │  POST /tracked, GET /prices  │
│  alerts · POST /webhooks/price-drop ◄──┼──── webhook assinado (HMAC) ─┤
└───────────────┬────────────────────────┘                              │
                │                                                       ▼
          ┌─────▼──────┐                         ┌──────────────────────────────┐
          │ MySQL      │                         │  Serviço de Preços (FastAPI) │
          │ wishlist   │                         │  tracked · prices · check    │
          └────────────┘                         └───────┬──────────────▲───────┘
                                                         │              │
                                       REST (GET)        │              │ POST /check (HMAC)
                                                         ▼              │ a cada 6 horas
          ┌────────────┐                         ┌──────────────┐  ┌────┴───────────┐
          │ MySQL      │◄── Serviço de Preços    │  CheapShark  │  │ GitHub Actions │
          │ prices     │                         │  (externa)   │  │  (agendador)   │
          └────────────┘                         └──────────────┘  └────────────────┘
```

Arquitetura distribuída baseada em serviços: cada serviço tem código, deploy e banco próprios, e os dados só circulam pelas APIs.

| Sistema | Tipo | Papel |
|---|---|---|
| **Wishlist API** ([`src/`](src/)) | Próprio | Usuários, login, catálogo de jogos, wishlist e alertas |
| **Serviço de Preços** ([`price_service/`](price_service/)) | Próprio | Monitora os preços na CheapShark, guarda o histórico e avisa a Wishlist API das quedas |
| **Frontend** ([`frontend/`](frontend/)) | Próprio (cliente) | Interface em Streamlit; só conversa com a Wishlist API |
| **CheapShark** ([apidocs.cheapshark.com](https://apidocs.cheapshark.com/)) | Externo | Preços de jogos de PC em várias lojas (Steam, GOG, Green Man Gaming...) |
| **GitHub Actions** ([`.github/workflows/check-prices.yml`](.github/workflows/check-prices.yml)) | Agendador | Dispara a verificação de preços a cada 6 horas |

### Integrações

| De → Para | Padrão | Para quê |
|---|---|---|
| Wishlist API → Serviço de Preços | **REST/JSON síncrono**, assinado com HMAC | Começar/parar de monitorar um jogo e buscar o preço atual |
| Serviço de Preços → Wishlist API | **Webhook** (orientado a eventos), assinado com HMAC | Avisar que um preço caiu |
| Serviço de Preços → CheapShark | **REST/JSON** (API externa pública) | Buscar o jogo e os preços nas lojas |
| GitHub Actions → Serviço de Preços | REST, assinado com HMAC | Disparar a verificação periódica (`POST /check`) |

Por que essas escolhas (e não mensageria, por exemplo) está explicado no guia da equipe e resumido em [Decisões](#decisões).

### Fluxo principal

1. O usuário adiciona um jogo à wishlist (`POST /wishlist`).
2. A Wishlist API responde na hora e, em segundo plano, chama `POST /tracked` no Serviço de Preços.
3. O Serviço de Preços procura o jogo na CheapShark pelo título, guarda o `gameID` dela e o preço atual.
4. Na tela da wishlist (`GET /wishlist`), a Wishlist API busca os preços de todos os jogos numa chamada só (`GET /prices?game_ids=...`).
5. A cada 6 horas, o GitHub Actions chama `POST /check`. O Serviço de Preços consulta a CheapShark para todos os jogos monitorados (em lotes de 25).
6. Se um preço caiu, o Serviço de Preços grava o aviso no *outbox* e chama `POST /webhooks/price-drop` na Wishlist API.
7. A Wishlist API cria um alerta para cada usuário com aquele jogo na wishlist, e ele aparece em `GET /alerts` (aba **Alertas** do Streamlit).

### Consistência e segurança da troca de dados

- **HMAC em toda chamada entre serviços:** prova a origem, impede alterar corpo ou rota e recusa requisições com mais de 5 minutos. Detalhes em [docs/autenticacao.md](docs/autenticacao.md).
- **Validação com Pydantic** de tudo que entra (inclusive o corpo do webhook).
- **Webhook idempotente:** cada aviso tem um `event_id` (jogo + loja + preço + dia). A Wishlist API ignora um `event_id` repetido para o mesmo usuário (índice único), então reenviar nunca duplica alertas.
- **Outbox com reenvio:** todo aviso é gravado antes do envio. Se a Wishlist API estiver fora do ar, ele fica pendente e é reenviado no próximo `/check`.
- **Degradação controlada:** se o Serviço de Preços estiver fora do ar, a wishlist continua funcionando e o preço aparece como indisponível (`price_status: "unavailable"`). Se ele não conhecer um jogo, a Wishlist API pede para monitorá-lo de novo.
- **HTTPS** em todos os serviços no Render.

---

## Tecnologias Utilizadas

| Categoria | Tecnologia |
|---|---|
| Linguagem | Python |
| Framework Web | FastAPI (nos dois serviços) |
| Servidor ASGI | Uvicorn |
| ORM & Banco de Dados | SQLAlchemy e MySQL (PyMySQL) na Aiven |
| Validação de Dados | Pydantic |
| Cliente HTTP | requests |
| Hash de Senhas | pwdlib (Argon2) |
| Sessão | Cookie assinado (itsdangerous) |
| Autenticação entre serviços | HMAC-SHA256 (biblioteca padrão `hmac`) |
| API externa | CheapShark |
| Agendamento | GitHub Actions (workflow com `schedule`) |
| Frontend | Streamlit |
| Deploy | Render (3 Web Services) |

---

## Ambiente Deployado

| Serviço | URL |
|---|---|
| Wishlist API | `https://sistema-de-wishlist.onrender.com` (Swagger em `/docs`) |
| Serviço de Preços | `https://<nome-do-servico>.onrender.com` (Swagger em `/docs`) |
| Frontend | `https://<nome-do-frontend>.onrender.com` |

No plano grátis do Render, cada serviço dorme depois de 15 minutos sem uso e leva até 1 minuto para acordar.

### Deploy no Render

Os três serviços são **Web Services** apontando para este mesmo repositório (deploy automático a cada push na `main`).

| Campo | Wishlist API | Serviço de Preços | Frontend |
|---|---|---|---|
| Root Directory | *(vazio)* | `price_service` | `frontend` |
| Build Command | `pip install -r requirements.txt` | `pip install -r requirements.txt` | `pip install -r requirements.txt` |
| Start Command | `cd src && uvicorn main:app --host 0.0.0.0 --port $PORT` | `uvicorn main:app --host 0.0.0.0 --port $PORT` | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |

### Variáveis de Ambiente

**Wishlist API**

```env
# Banco de dados (Aiven)
DB_HOST=host_do_banco
DB_PORT=porta_do_banco
DB_USER=usuario_do_banco
DB_PASSWORD=senha_do_banco
DB_NAME=wishlist
DB_SSL_CA=ca.pem

# Autenticação
SECRET_KEY=chave_secreta_dos_cookies
INTERNAL_SECRET=chave_compartilhada_entre_os_servicos

# Integração
PRICE_SERVICE_URL=https://<nome-do-servico>.onrender.com
PRICE_SERVICE_TIMEOUT=10   # opcional, em segundos
```

**Serviço de Preços**

```env
# Banco de dados: mesma instância da Aiven, outro banco
DB_HOST=host_do_banco
DB_PORT=porta_do_banco
DB_USER=usuario_do_banco
DB_PASSWORD=senha_do_banco
DB_NAME=prices
DB_SSL_CA=ca.pem

# Integração
INTERNAL_SECRET=chave_compartilhada_entre_os_servicos
WISHLIST_API_URL=https://sistema-de-wishlist.onrender.com
CHEAPSHARK_USER_AGENT=WishlistAV3/1.0   # opcional; a CheapShark recusa User-Agent genérico
```

**Frontend**

```env
API_URL=https://sistema-de-wishlist.onrender.com
```

Para gerar as chaves: `python -c "import secrets; print(secrets.token_hex(32))"`. O `INTERNAL_SECRET` precisa ser **igual** nos dois serviços e no GitHub Actions.

Variáveis opcionais, para o ambiente local:

```env
COOKIE_SECURE=false            # permite o cookie de sessão em http://localhost
DATABASE_URL=sqlite:///dev.db  # usa um SQLite local em vez do MySQL (vale para os dois serviços)
```

### GitHub Actions

O workflow [`check-prices.yml`](.github/workflows/check-prices.yml) roda nos servidores do GitHub a cada 6 horas: acorda os dois serviços e chama `POST /check` com a assinatura HMAC. Ele precisa de três secrets em **Settings → Secrets and variables → Actions**:

| Secret | Valor |
|---|---|
| `INTERNAL_SECRET` | A mesma chave dos serviços |
| `PRICE_SERVICE_URL` | URL do Serviço de Preços no Render |
| `WISHLIST_API_URL` | URL da Wishlist API no Render |

Para rodar na hora (ex.: na apresentação): aba **Actions** → **Verificar preços** → **Run workflow**.

O horário do `cron` é em UTC e o GitHub pode atrasar alguns minutos. Em repositórios sem commits há 60 dias, o GitHub desativa workflows agendados.

---

## Executando localmente

```bash
pip install -r requirements.txt

# Terminal 1: Wishlist API (porta 8000)
cd src && uvicorn main:app --reload --port 8000

# Terminal 2: Serviço de Preços (porta 8001)
cd price_service && uvicorn main:app --reload --port 8001

# Terminal 3: Frontend
pip install -r frontend/requirements.txt
streamlit run frontend/app.py
```

Cada serviço lê o próprio `.env`: a Wishlist API usa o `.env` da raiz e o Serviço de Preços usa o `price_service/.env` (com `DB_NAME=prices` e o mesmo `INTERNAL_SECRET`). Os dois ficam fora do Git.

Sem as variáveis de URL, a Wishlist API procura o Serviço de Preços em `http://localhost:8001`, o Serviço de Preços avisa a Wishlist API em `http://localhost:8000` e o frontend usa `http://localhost:8000`.

Para disparar a verificação de preços localmente (o mesmo que o GitHub Actions faz):

```bash
TS=$(date +%s)
SIG=$(printf '%s\nPOST\n/check\n' "$TS" | openssl dgst -sha256 -hmac "$INTERNAL_SECRET" -r | cut -d' ' -f1)
curl -X POST http://localhost:8001/check -H "X-Timestamp: $TS" -H "X-Signature: sha256=$SIG"
```

---

## Banco de Dados

Os dois serviços usam a mesma instância MySQL da Aiven, mas **bancos separados**: um serviço nunca lê as tabelas do outro.

> **Migrações:** o SQLAlchemy cria as tabelas que não existem, mas não adiciona nem remove colunas de tabelas já criadas.
> - Wishlist API: [`migrations/001_auth.sql`](migrations/001_auth.sql) e [`migrations/002_otp.sql`](migrations/002_otp.sql) (já rodadas na AV2). [`migrations/003_remove_otp.sql`](migrations/003_remove_otp.sql) remove as colunas do SMS (opcional). A tabela `alerts` é criada sozinha.
> - Serviço de Preços: rodar uma vez [`price_service/migrations.sql`](price_service/migrations.sql) (`CREATE DATABASE prices`). As tabelas são criadas sozinhas na primeira subida.

### Banco `wishlist` (Wishlist API)

**Tabela `users`**

| Campo | Tipo |
|---|---|
| id | int, primary key, auto-increment |
| username | varchar |
| email | varchar, único |
| password | varchar (hash Argon2) |
| phone | varchar, opcional (formato `+5582999999999`) |
| role | varchar (`admin` ou `user`) |
| session_version | int |
| created_at | date |
| last_update | date |

**Tabela `games`**

| Campo | Tipo |
|---|---|
| id | int, primary key, auto-increment |
| title | varchar |
| genre | varchar |
| platform | varchar |
| release_date | date |
| created_at | date |
| last_update | date |

**Tabela `wishlist`**

| Campo | Tipo |
|---|---|
| id | int, primary key, auto-increment |
| user_id | int, foreign key → users.id |
| game_id | int, foreign key → games.id |
| created_at | date |
| last_update | date |

**Tabela `alerts`**

| Campo | Tipo |
|---|---|
| id | int, primary key, auto-increment |
| user_id | int, foreign key → users.id |
| game_id | int, foreign key → games.id |
| event_id | varchar (único junto com `user_id`) |
| old_price, new_price, normal_price | decimal (USD) |
| store | varchar |
| deal_url | varchar |
| currency | varchar (`USD`) |
| created_at | datetime |

### Banco `prices` (Serviço de Preços)

**Tabela `tracked_games`**: um registro por jogo monitorado. `game_id` é o mesmo id da Wishlist API; `cheapshark_id` e `steam_app_id` vêm da CheapShark; guarda o preço atual, o preço normal, a loja, a oferta e o menor preço histórico.

**Tabela `price_history`**: um registro a cada mudança de preço (jogo, preço, preço normal, loja, data).

**Tabela `webhook_outbox`**: avisos de queda de preço, com `event_id` único, tentativas, último erro e data de entrega.

---

## Frontend (Streamlit)

Interface web em [`frontend/app.py`](frontend/app.py). Ela não acessa o banco: conversa com a Wishlist API por HTTP, como qualquer outro cliente, e guarda o cookie de sessão da API para cada pessoa conectada.

| Papel | Telas |
|---|---|
| `user` | Catálogo (com botão para adicionar à wishlist), Minha wishlist (com o preço atual de cada jogo) e Alertas |
| `admin` | Catálogo, Gerenciar jogos (adicionar, editar, remover) e Usuários (alterar papel) |

---

## Autenticação

A API não usa OAuth2 nem Bearer Token. Detalhes em [docs/autenticacao.md](docs/autenticacao.md).

- **Usuários:** email e senha (Argon2). A sessão fica num **cookie assinado**, sem estado guardado no servidor. O código por SMS da AV2 foi removido.
- **Entre serviços:** assinatura **HMAC-SHA256** em cada requisição, com uma chave compartilhada (`INTERNAL_SECRET`).

### Tipos de usuário

| Papel | Permissões |
|---|---|
| `admin` | Adicionar, editar e remover jogos do catálogo; listar usuários; alterar papéis |
| `user` | Adicionar, listar e remover jogos da própria wishlist; ver e dispensar os próprios alertas |

Todo cadastro cria um `user`. Um admin pode promover outros usuários pelo `PATCH /users/{id}/role`; o primeiro admin é criado direto no banco:

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@email.com';
```

---

## Endpoints da Wishlist API

Base: `https://sistema-de-wishlist.onrender.com`. A coluna **Acesso** indica quem pode usar cada rota (sem login → `401`; sem permissão → `403`).

### Autenticação

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/auth/login` | Confere email e senha e devolve o cookie de sessão | Público |
| GET | `/auth/me` | Dados do usuário logado | Logado |
| POST | `/auth/logout` | Encerra a sessão neste navegador | Público |
| POST | `/auth/logout-all` | Encerra a sessão em todos os dispositivos | Logado |

### Usuários

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/users` | Criar um novo usuário | Público |
| GET | `/users` | Listar todos os usuários | Admin |
| GET | `/users/{id}` | Obter detalhes de um usuário | Próprio usuário ou admin |
| PUT | `/users/{id}` | Atualizar informações de um usuário | Próprio usuário |
| PATCH | `/users/{id}/role` | Alterar o papel de um usuário | Admin |
| DELETE | `/users/{id}` | Deletar um usuário | Próprio usuário ou admin |

### Jogos

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/games` | Adicionar um novo jogo | Admin |
| GET | `/games` | Listar todos os jogos | Público |
| GET | `/games/{id}` | Obter detalhes de um jogo | Público |
| PUT | `/games/{id}` | Atualizar um jogo (se o título mudar, o Serviço de Preços procura o jogo de novo) | Admin |
| DELETE | `/games/{id}` | Deletar um jogo (e parar de monitorar o preço) | Admin |

### Wishlist

Todas as rotas agem sobre a wishlist do usuário logado. Itens de outros usuários respondem `404`.

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/wishlist` | Adicionar um jogo à wishlist (e começar a monitorar o preço) | User |
| GET | `/wishlist` | Listar a wishlist, com o preço atual de cada jogo | User |
| GET | `/wishlist/{id}` | Obter um item da wishlist | User |
| DELETE | `/wishlist/{id}` | Remover um jogo (se ninguém mais o tiver, para de monitorar) | User |

### Alertas e webhook

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| GET | `/alerts` | Alertas de queda de preço do usuário, do mais recente ao mais antigo | User |
| DELETE | `/alerts/{id}` | Dispensar um alerta | User |
| POST | `/webhooks/price-drop` | Recebe o aviso de queda de preço do Serviço de Preços | Assinatura HMAC |

## Endpoints do Serviço de Preços

Todas as rotas, menos `GET /`, exigem a assinatura HMAC (`X-Timestamp` e `X-Signature`). Preços sempre em dólar.

| Método | Rota | Quem chama | Descrição |
|---|---|---|---|
| GET | `/` | Qualquer um | Status (usado para acordar o serviço) |
| POST | `/tracked` | Wishlist API | Começa a monitorar um jogo `{game_id, title}`: procura na CheapShark e já busca o preço. Chamar de novo não duplica |
| DELETE | `/tracked/{game_id}` | Wishlist API | Para de monitorar o jogo |
| GET | `/prices?game_ids=1,2,3` | Wishlist API | Preços de vários jogos numa chamada |
| GET | `/prices/{game_id}` | Wishlist API | Preço atual, loja, desconto e menor preço histórico |
| GET | `/prices/{game_id}/history` | Wishlist API | Histórico de preços registrados |
| POST | `/check` | GitHub Actions | Consulta a CheapShark para todos os jogos e dispara o webhook para cada queda |

### Exemplo: corpo do webhook `POST /webhooks/price-drop`

```json
{
  "event_id": "1-23-14.96-20261125",
  "game_id": 1,
  "title": "Red Dead Redemption 2",
  "old_price": 59.99,
  "new_price": 14.96,
  "normal_price": 59.99,
  "savings_percent": 75.1,
  "store": "GameBillet",
  "deal_url": "https://www.cheapshark.com/redirect?dealID=...",
  "currency": "USD",
  "detected_at": "2026-11-25T20:39:14"
}
```

### Exemplo: resposta de `POST /check`

```json
{ "checked": 12, "newly_found": 1, "price_drops": 2, "delivered": 2, "pending": 0, "errors": [] }
```

---

## Como Testar a API (Guia para Clientes HTTP)

Use qualquer cliente HTTP (Postman, Insomnia, Thunder Client, cURL etc.).

> **Atenção:** nas requisições que enviam dados (POST, PUT e PATCH), configure o header `Content-Type: application/json`.

> **Sessão:** o login devolve um cookie `session`. O Swagger (`/docs`), o Postman e o Insomnia guardam e reenviam o cookie automaticamente; no cURL use `-c cookies.txt` para salvar e `-b cookies.txt` para enviar.

**1. Criando um Usuário (`POST /users`)**

```json
{
  "username": "Victor",
  "email": "victor@email.com",
  "password": "senha_segura"
}
```
*Retorno esperado: `201 Created` com os dados gerados (papel `user`).*

**2. Fazendo Login (`POST /auth/login`)**

```json
{
  "email": "victor@email.com",
  "password": "senha_segura"
}
```
*Retorno esperado: `200 OK` e o cookie de sessão, que libera as rotas protegidas.*

**3. Adicionando um Jogo — admin (`POST /games`)**

```json
{
  "title": "Red Dead Redemption 2",
  "genre": "Ação",
  "platform": "PC",
  "release_date": "2019-11-05"
}
```
*Retorno esperado: `201 Created`. Para o preço ser encontrado, o título deve ser o nome do jogo nas lojas.*

**4. Adicionando um Jogo à Wishlist — user (`POST /wishlist`)**

```json
{
  "game_id": 1
}
```
*Retorno esperado: `201 Created`. Em segundo plano, o Serviço de Preços começa a monitorar o jogo. Se já estiver na wishlist, `409 Conflict`.*

**5. Vendo a Wishlist com Preços — user (`GET /wishlist`)**

```json
[
  {
    "id": 1,
    "user_id": 2,
    "game_id": 1,
    "created_at": "2026-11-25",
    "last_update": "2026-11-25",
    "price": {
      "found": true,
      "current_price": 14.96,
      "normal_price": 59.99,
      "savings_percent": 75.1,
      "store": "GameBillet",
      "deal_url": "https://www.cheapshark.com/redirect?dealID=...",
      "cheapest_ever": 12.0,
      "currency": "USD",
      "last_checked_at": "2026-11-25T20:39:06"
    },
    "price_status": "ok"
  }
]
```
*`price_status` pode ser `ok`, `not_tracked` (o preço ainda está sendo buscado) ou `unavailable` (Serviço de Preços fora do ar).*

**6. Promovendo um Usuário a Admin — admin (`PATCH /users/{id}/role`)**

```json
{
  "role": "admin"
}
```
*Retorno esperado: `200 OK`.*

Para os endpoints `GET` e `DELETE`, não é preciso corpo JSON; basta o ID na URL (ex.: `DELETE /games/1`).

---

## Decisões

- **Dois serviços:** monitorar preços é uma responsabilidade diferente de cuidar de usuários e listas (agendamento, histórico, API externa). Separados, uma falha na CheapShark não derruba o login nem a wishlist.
- **REST num sentido, webhook no outro:** a Wishlist precisa do preço na hora (síncrono). A queda de preço é um evento raro que nasce no Serviço de Preços, então ele avisa quando acontece, em vez de a Wishlist ficar perguntando (polling).
- **Sem mensageria (RabbitMQ, Kafka):** seria mais um componente para hospedar, o Render free não roda processos em segundo plano e o volume é pequeno. O webhook com outbox, reenvio e idempotência já garante a entrega.
- **CheapShark:** grátis, sem chave, várias lojas, com preço atual, desconto e menor preço histórico. A API da Steam cobre só a Steam, a IsThereAnyDeal exige chave e a RAWG não tem preços. Limites aceitos: preços só em dólar e limite de requisições (por isso as consultas são em lote e só o Serviço de Preços fala com ela).
- **GitHub Actions como agendador:** o Render free dorme e o cron do Render é pago; o Actions é grátis e fica no mesmo repositório.
