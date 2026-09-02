# sistema_de_wishlist

## Descrição do Projeto
Desenvolver um sistema básico de wishlist de jogos, onde os usuários podem adicionar jogos que desejam comprar ou jogar no futuro. O sistema permitirá que os usuários criem uma lista de desejos personalizada, visualizem os jogos adicionados e removam jogos da lista conforme necessário.

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
