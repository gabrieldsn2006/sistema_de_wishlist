# Sistema de Wishlist de Jogos - API REST

## Equipe

- Victor Lins Gurgel do Amaral
- Lorenzo Barros Calheiros Pinheiro
- Gabriel De Sousa Nobre

## Descrição do Projeto

Desenvolver um sistema básico de wishlist de jogos, onde os usuários podem adicionar jogos que desejam comprar ou jogar no futuro. O sistema permitirá que os usuários criem uma lista de desejos personalizada, visualizem os jogos adicionados e removam jogos da lista conforme necessário.

## Tecnologias Utilizadas

| Categoria | Tecnologia |
|---|---|
| Linguagem | Python |
| Framework Web | FastAPI |
| ORM & Banco de Dados | SQLAlchemy e MySQL (PyMySQL) |
| Servidor ASGI | Uvicorn |
| Validação de Dados | Pydantic |
| Hash de Senhas | pwdlib (Argon2) |
| Sessão | Cookie assinado (itsdangerous) |
| Código por SMS (2FA) | Twilio Verify |
| Frontend | Streamlit |

## Ambiente Deployado

### API

O servidor está hospedado no Render e pode ser acessado pela URL pública:

`https://sistema-de-wishlist.onrender.com`

Documentação interativa:

- Swagger UI: `https://sistema-de-wishlist.onrender.com/docs`
- ReDoc: `https://sistema-de-wishlist.onrender.com/redoc`

### Banco de Dados

O banco de dados MySQL está hospedado na Aiven.

### Variáveis de Ambiente

As configurações são definidas nas variáveis de ambiente do serviço deployado (e no arquivo `.env`, no ambiente local):

```env
# Banco de dados
DB_HOST=host_do_banco
DB_PORT=porta_do_banco
DB_USER=usuario_do_banco
DB_PASSWORD=senha_do_banco
DB_NAME=wishlist
DB_SSL_CA=ca.pem

# Autenticação
SECRET_KEY=chave_secreta_dos_cookies

# Código por SMS (Twilio Verify)
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=account_sid_do_twilio
TWILIO_AUTH_TOKEN=auth_token_do_twilio
TWILIO_VERIFY_SERVICE_SID=sid_do_verify_service
```

Variáveis opcionais, para o ambiente local:

```env
COOKIE_SECURE=false   # permite o cookie de sessão em http://localhost
SMS_DEV_MODE=true     # imprime o código de verificação no log em vez de enviar SMS
```

---

## Banco de Dados

O projeto utiliza um banco de dados MySQL hospedado na Aiven. A estrutura do banco é a seguinte:

> **Migrações:** o SQLAlchemy cria as tabelas que não existem, mas não adiciona colunas a tabelas já criadas. Por isso, as colunas da autenticação devem ser adicionadas rodando, uma vez e nesta ordem, os scripts [`migrations/001_auth.sql`](migrations/001_auth.sql) e [`migrations/002_otp.sql`](migrations/002_otp.sql).

### Tabela `users`

| Campo | Tipo |
|---|---|
| id | int, primary key, auto-increment |
| username | varchar |
| email | varchar |
| password | varchar (hash Argon2) |
| phone | varchar (formato `+5582999999999`) |
| role | varchar (`admin` ou `user`) |
| session_version | int |
| otp_hash | varchar |
| otp_expires_at | datetime |
| otp_attempts | int |
| created_at | date |
| last_update | date |

### Tabela `games`

| Campo | Tipo |
|---|---|
| id | int, primary key, auto-increment |
| title | varchar |
| genre | varchar |
| platform | varchar |
| release_date | date |
| created_at | date |
| last_update | date |

### Tabela `wishlist`

| Campo | Tipo |
|---|---|
| id | int, primary key, auto-increment |
| user_id | int, foreign key referencing users.id |
| game_id | int, foreign key referencing games.id |
| created_at | date |
| last_update | date |

---

## Frontend (Streamlit)

Interface web básica em [`frontend/app.py`](frontend/app.py), feita com Streamlit. Ela não acessa o banco: conversa com a API por HTTP, como qualquer outro cliente, e guarda o cookie de sessão da API para cada pessoa conectada.

| Papel | Telas |
|---|---|
| `user` | Catálogo (com botão para adicionar à wishlist) e Minha wishlist |
| `admin` | Catálogo, Gerenciar jogos (adicionar, editar, remover) e Usuários (alterar papel) |

### Rodando localmente

```bash
pip install -r frontend/requirements.txt
API_URL=http://localhost:8000 streamlit run frontend/app.py
```

Sem `API_URL`, o frontend usa `http://localhost:8000`.

### Deploy no Render

O frontend é um **segundo Web Service** no Render, apontando para este mesmo repositório:

| Campo | Valor |
|---|---|
| Root Directory | `frontend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `streamlit run app.py --server.port $PORT --server.address 0.0.0.0` |
| Variável de ambiente | `API_URL=https://sistema-de-wishlist.onrender.com` |

---

## Autenticação

A API não usa OAuth2 nem Bearer Token. O login é feito em duas etapas (senha + código por SMS) e a sessão fica num **cookie assinado**, sem estado guardado no servidor. Detalhes em [docs/autenticacao.md](docs/autenticacao.md).

### Tipos de usuário

| Papel | Permissões |
|---|---|
| `admin` | Adicionar, editar e remover jogos do catálogo; listar usuários; alterar papéis |
| `user` | Adicionar, listar e remover jogos da própria wishlist |

Todo cadastro cria um `user`. Um admin pode promover outros usuários pelo `PATCH /users/{id}/role`; o primeiro admin é criado direto no banco:

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@email.com';
```

### Endpoints de autenticação

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Confere email e senha e envia o código por SMS |
| POST | `/auth/verify` | Confere o código do SMS e conclui o login |
| GET | `/auth/me` | Dados do usuário logado |
| POST | `/auth/logout` | Encerra a sessão neste navegador |
| POST | `/auth/logout-all` | Encerra a sessão em todos os dispositivos |

---

## Endpoints da API

CRUD de usuários, jogos e wishlist. A coluna **Acesso** indica quem pode usar cada rota (sem login → `401`; sem permissão → `403`).

### Endpoints de usuários

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `https://sistema-de-wishlist.onrender.com/users` | Criar um novo usuário | Público |
| GET | `https://sistema-de-wishlist.onrender.com/users` | Listar todos os usuários | Admin |
| GET | `https://sistema-de-wishlist.onrender.com/users/{id}` | Obter detalhes de um usuário específico | Próprio usuário ou admin |
| PUT | `https://sistema-de-wishlist.onrender.com/users/{id}` | Atualizar informações de um usuário | Próprio usuário |
| PATCH | `https://sistema-de-wishlist.onrender.com/users/{id}/role` | Alterar o papel de um usuário | Admin |
| DELETE | `https://sistema-de-wishlist.onrender.com/users/{id}` | Deletar um usuário | Próprio usuário ou admin |

### Endpoints de jogos

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `https://sistema-de-wishlist.onrender.com/games` | Adicionar um novo jogo | Admin |
| GET | `https://sistema-de-wishlist.onrender.com/games` | Listar todos os jogos | Público |
| GET | `https://sistema-de-wishlist.onrender.com/games/{id}` | Obter detalhes de um jogo específico | Público |
| PUT | `https://sistema-de-wishlist.onrender.com/games/{id}` | Atualizar informações de um jogo | Admin |
| DELETE | `https://sistema-de-wishlist.onrender.com/games/{id}` | Deletar um jogo | Admin |

### Endpoints de wishlist

Todas as rotas agem sobre a wishlist do usuário logado. Itens de outros usuários respondem `404`.

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `https://sistema-de-wishlist.onrender.com/wishlist` | Adicionar um jogo à própria wishlist | User |
| GET | `https://sistema-de-wishlist.onrender.com/wishlist` | Listar os jogos da própria wishlist | User |
| GET | `https://sistema-de-wishlist.onrender.com/wishlist/{id}` | Obter um item específico da wishlist | User |
| DELETE | `https://sistema-de-wishlist.onrender.com/wishlist/{id}` | Remover um jogo da wishlist | User |

---

## Como Testar a API (Guia para Clientes HTTP)

Para testar a API, você pode utilizar qualquer programa de testes de API (como Postman, Insomnia, Thunder Client, cURL, etc.).

> **Atenção:** Para as requisições que enviam dados (POST, PUT e PATCH), certifique-se de configurar o cabeçalho (Header) da requisição com:
> ```
> Content-Type: application/json
> ```

> **Sessão:** o login devolve um cookie `session`. O Swagger (`/docs`), o Postman e o Insomnia guardam e reenviam o cookie automaticamente; no cURL use `-c cookies.txt` para salvar e `-b cookies.txt` para enviar.

### Exemplos de Corpo da Requisição (Body - JSON)

**1. Criando um Usuário (`POST https://sistema-de-wishlist.onrender.com/users`)**

```bash
{
  "username": "Victor",
  "email": "victor@email.com",
  "password": "senha_segura",
  "phone": "+5585999991111"
}
```
*Retorno esperado: Status `201 Created` com os dados gerados (papel `user`). O telefone precisa estar no formato internacional, pois recebe o código de login.*

**2. Fazendo Login (`POST https://sistema-de-wishlist.onrender.com/auth/login`)**

```bash
{
  "email": "victor@email.com",
  "password": "senha_segura"
}
```
*Retorno esperado: Status `200 OK`, cookie de sessão pendente e um SMS com o código de 6 dígitos.*

**3. Confirmando o Código (`POST https://sistema-de-wishlist.onrender.com/auth/verify`)**

```bash
{
  "code": "482913"
}
```
*Retorno esperado: Status `200 OK`. A partir daqui o cookie libera as rotas protegidas. O código vale 5 minutos e aceita até 5 tentativas.*

**4. Atualizando o Próprio Usuário (`PUT https://sistema-de-wishlist.onrender.com/users/{id}`)**

```bash
{
  "phone": "+5585900000000"
}
```
*Retorno esperado: Status `200 OK` com os dados atualizados.*

**5. Adicionando um Jogo — admin (`POST https://sistema-de-wishlist.onrender.com/games`)**

```bash
{
  "title": "Hollow Knight",
  "genre": "Metroidvania",
  "platform": "PC",
  "release_date": "2017-02-24"
}
```
*Retorno esperado: Status `201 Created`.*

**6. Adicionando um Jogo à Wishlist — user (`POST https://sistema-de-wishlist.onrender.com/wishlist`)**

```bash
{
  "game_id": 1
}
```
*Retorno esperado: Status `201 Created`. O jogo entra na wishlist do usuário logado; se já estiver lá, `409 Conflict`.*

**7. Promovendo um Usuário a Admin — admin (`PATCH https://sistema-de-wishlist.onrender.com/users/{id}/role`)**

```bash
{
  "role": "admin"
}
```
*Retorno esperado: Status `200 OK`.*

Para os endpoints do tipo `GET` e `DELETE`, não é necessário enviar um corpo JSON; basta acessar a rota especificando o ID diretamente na URL (exemplo: `DELETE https://sistema-de-wishlist.onrender.com/games/1`).