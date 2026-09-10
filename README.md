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

## Ambiente Deployado

### API

O servidor está hospedado no Render e pode ser acessado pela URL pública:

`https://sistema-de-wishlist.onrender.com`

Documentação interativa:

- Swagger UI: `https://sistema-de-wishlist.onrender.com/docs`
- ReDoc: `https://sistema-de-wishlist.onrender.com/redoc`

### Banco de Dados

O banco de dados MySQL está hospedado na Aiven. As configurações são definidas nas variáveis de ambiente do serviço deployado:

```env
DB_HOST=host_do_banco
DB_PORT=porta_do_banco
DB_USER=usuario_do_banco
DB_PASSWORD=senha_do_banco
DB_NAME=wishlist
DB_SSL_CA=ca.pem
```

---

## Banco de Dados

O projeto utiliza um banco de dados MySQL hospedado na Aiven. A estrutura do banco é a seguinte:

### Tabela `users`

| Campo | Tipo |
|---|---|
| id | int, primary key, auto-increment |
| username | varchar |
| email | varchar |
| password | varchar |
| phone | varchar |
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

## Endpoints da API

CRUD de usuários, jogos e wishlist.

### Endpoints de usuários

| Método | Rota | Descrição |
|---|---|---|
| POST | `https://sistema-de-wishlist.onrender.com/users` | Criar um novo usuário |
| GET | `https://sistema-de-wishlist.onrender.com/users` | Listar todos os usuários |
| GET | `https://sistema-de-wishlist.onrender.com/users/{id}` | Obter detalhes de um usuário específico |
| PUT | `https://sistema-de-wishlist.onrender.com/users/{id}` | Atualizar informações de um usuário |
| DELETE | `https://sistema-de-wishlist.onrender.com/users/{id}` | Deletar um usuário |

### Endpoints de jogos

| Método | Rota | Descrição |
|---|---|---|
| POST | `https://sistema-de-wishlist.onrender.com/games` | Adicionar um novo jogo |
| GET | `https://sistema-de-wishlist.onrender.com/games` | Listar todos os jogos |
| GET | `https://sistema-de-wishlist.onrender.com/games/{id}` | Obter detalhes de um jogo específico |
| PUT | `https://sistema-de-wishlist.onrender.com/games/{id}` | Atualizar informações de um jogo |
| DELETE | `https://sistema-de-wishlist.onrender.com/games/{id}` | Deletar um jogo |

### Endpoints de wishlist

| Método | Rota | Descrição |
|---|---|---|
| POST | `https://sistema-de-wishlist.onrender.com/wishlist` | Adicionar um jogo à wishlist de um usuário |
| GET | `https://sistema-de-wishlist.onrender.com/wishlist/{user_id}` | Listar todos os jogos na wishlist de um usuário específico |
| DELETE | `https://sistema-de-wishlist.onrender.com/wishlist/{id}` | Remover um jogo da wishlist |

---

## Como Testar a API (Guia para Clientes HTTP)

Para testar a API, você pode utilizar qualquer programa de testes de API (como Postman, Insomnia, Thunder Client, cURL, etc.).

> **Atenção:** Para as requisições que enviam dados (POST e PUT), certifique-se de configurar o cabeçalho (Header) da requisição com:
> ```
> Content-Type: application/json
> ```

### Exemplos de Corpo da Requisição (Body - JSON)

**1. Criando um Usuário (`POST https://sistema-de-wishlist.onrender.com/users`)**

```bash
{
  "username": "Victor",
  "email": "victor@email.com",
  "password": "senha_segura",
  "phone": "85999991111"
}
```
*Retorno esperado: Status `201 Created` com os dados gerados.*

**2. Atualizando um Usuário (`PUT https://sistema-de-wishlist.onrender.com/users/{id}`)**

```bash
{
  "phone": "85900000000"
}
```
*Retorno esperado: Status `200 OK` com os dados atualizados.*

**3. Adicionando um Jogo (`POST https://sistema-de-wishlist.onrender.com/games`)**

```bash
{
  "title": "Hollow Knight",
  "genre": "Metroidvania",
  "platform": "PC",
  "release_date": "2017-02-24"
}
```
*Retorno esperado: Status `201 Created`.*

**4. Adicionando um Jogo à Wishlist (`POST https://sistema-de-wishlist.onrender.com/wishlist`)**

```bash
{
  "user_id": 1,
  "game_id": 1
}
```
*Retorno esperado: Status `201 Created`.*

Para os endpoints do tipo `GET` e `DELETE`, não é necessário enviar um corpo JSON; basta acessar a rota especificando o ID diretamente na URL (exemplo: `DELETE https://sistema-de-wishlist.onrender.com/games/1`).