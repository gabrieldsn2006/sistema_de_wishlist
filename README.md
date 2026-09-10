# Sistema de Wishlist de Jogos - API REST

## Equipe
* Victor Lins Gurgel do Amaral
* Lorenzo Barros Calheiros Pinheiro
* Gabriel De Sousa Nobre

## Descrição do Projeto

Desenvolver um sistema básico de wishlist de jogos, onde os usuários podem adicionar jogos que desejam comprar ou jogar no futuro. O sistema permitirá que os usuários criem uma lista de desejos personalizada, visualizem os jogos adicionados e removam jogos da lista conforme necessário.

## Tecnologias Utilizadas
* **Linguagem:** Python
* **Framework Web:** FastAPI
* **ORM & Banco de Dados:** SQLAlchemy e MySQL (PyMySQL)
* **Servidor ASGI:** Uvicorn
* **Validação de Dados:** Pydantic

## Como Executar Localmente

1. **Clone o repositório:**

```bash
   git clone https://github.com/gabrieldsn2006/sistema_de_wishlist
   cd src
```

2. **Instale as dependências:**

```bash
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv pydantic

```


3. **Configure o Banco de Dados:**
* Crie um banco de dados no MySQL Workbench chamado `wishlist`.
* Crie um arquivo `.env` na raiz do projeto com as seguintes credenciais:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=wishlist

```




4. **Inicie o servidor:**
```bash
python main.py

```


A documentação interativa (Swagger UI) estará disponível em: `http://127.0.0.1:8000/docs`

## Banco de Dados
Banco MySQL hospedado no Aiven. A estrutura do banco é a seguinte:
- Tabela `users`:
  - `id` (int, primary key, auto-increment)
  - `username` (varchar)
  - `email` (varchar)
  - `password` (varchar)
  - `phone` (varchar)
  - `created_at` (date)
  - `last_update` (date)
- Tabela `games`:
  - `id` (int, primary key, auto-increment)
  - `title` (varchar)
  - `genre` (varchar)
  - `platform` (varchar)
  - `release_date` (date)
  - `created_at` (date)
  - `last_update` (date)
- Tabela `wishlist`:
  - `id` (int, primary key, auto-increment)
  - `user_id` (int, foreign key referencing `users.id`)
  - `game_id` (int, foreign key referencing `games.id`)
  - `created_at` (date)
  - `last_update` (date)

## Endpoints da API
CRUD de usuários, jogos e wishlist.
- Endpoints de usuários:
  - `POST /users` - Criar um novo usuário
  - `GET /users` - Listar todos os usuários
  - `GET /users/{id}` - Obter detalhes de um usuário específico
  - `PUT /users/{id}` - Atualizar informações de um usuário
  - `DELETE /users/{id}` - Deletar um usuário
- Endpoints de jogos:
  - `POST /games` - Adicionar um novo jogo
  - `GET /games` - Listar todos os jogos
  - `GET /games/{id}` - Obter detalhes de um jogo específico
  - `PUT /games/{id}` - Atualizar informações de um jogo
  - `DELETE /games/{id}` - Deletar um jogo
- Endpoints de wishlist:
  - `POST /wishlist` - Adicionar um jogo à wishlist de um usuário
  - `GET /wishlist/{user_id}` - Listar todos os jogos na wishlist de um usuário específico
  - `DELETE /wishlist/{id}` - Remover um jogo da wishlist

