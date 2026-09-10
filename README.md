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

## Como Executar Localmente

### 1. Clone o repositório

```bash
git clone https://github.com/gabrieldsn2006/sistema_de_wishlist
cd src
```

### 2. Instale as dependências

```bash
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv pydantic
```

### 3. Configure o Banco de Dados

- Crie um banco de dados no MySQL Workbench chamado `wishlist`.
- Crie um arquivo `.env` na raiz do projeto com as seguintes credenciais:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=wishlist
```

### 4. Inicie o servidor

```bash
python main.py
```

A API estará disponível na base URL: `http://127.0.0.1:8000`

---

## Banco de Dados

O projeto utiliza um banco de dados MySQL que pode ser executado localmente ou em nuvem (como a Aiven). A estrutura do banco é a seguinte:

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
| POST | `/users` | Criar um novo usuário |
| GET | `/users` | Listar todos os usuários |
| GET | `/users/{id}` | Obter detalhes de um usuário específico |
| PUT | `/users/{id}` | Atualizar informações de um usuário |
| DELETE | `/users/{id}` | Deletar um usuário |

### Endpoints de jogos

| Método | Rota | Descrição |
|---|---|---|
| POST | `/games` | Adicionar um novo jogo |
| GET | `/games` | Listar todos os jogos |
| GET | `/games/{id}` | Obter detalhes de um jogo específico |
| PUT | `/games/{id}` | Atualizar informações de um jogo |
| DELETE | `/games/{id}` | Deletar um jogo |

### Endpoints de wishlist

| Método | Rota | Descrição |
|---|---|---|
| POST | `/wishlist` | Adicionar um jogo à wishlist de um usuário |
| GET | `/wishlist/{user_id}` | Listar todos os jogos na wishlist de um usuário específico |
| DELETE | `/wishlist/{id}` | Remover um jogo da wishlist |

---

## Como Testar a API (Guia para Clientes HTTP)

Para testar a API, você pode utilizar qualquer programa de testes de API (como Postman, Insomnia, Thunder Client, cURL, etc.).

> **Atenção:** Para as requisições que enviam dados (POST e PUT), certifique-se de configurar o cabeçalho (Header) da requisição com:
> ```
> Content-Type: application/json
> ```

### Exemplos de Corpo da Requisição (Body - JSON)

**1. Criando um Usuário (`POST /users`)**

```bash
{
  "username": "Victor",
  "email": "victor@email.com",
  "password": "senha_segura",
  "phone": "85999991111"
}
```
*Retorno esperado: Status `201 Created` com os dados gerados.*

**2. Atualizando um Usuário (`PUT /users/{id}`)**

```bash
{
  "phone": "85900000000"
}
```
*Retorno esperado: Status `200 OK` com os dados atualizados.*

**3. Adicionando um Jogo (`POST /games`)**

```bash
{
  "title": "Hollow Knight",
  "genre": "Metroidvania",
  "platform": "PC",
  "release_date": "2017-02-24"
}
```
*Retorno esperado: Status `201 Created`.*

**4. Adicionando um Jogo à Wishlist (`POST /wishlist`)**

```bash
{
  "user_id": 1,
  "game_id": 1
}
```
*Retorno esperado: Status `201 Created`.*

Para os endpoints do tipo `GET` e `DELETE`, não é necessário enviar um corpo JSON; basta acessar a rota especificando o ID diretamente na URL (exemplo: `DELETE http://127.0.0.1:8000/games/1`).