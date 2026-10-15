-- O create_all do SQLAlchemy não altera tabelas que já existem,
-- então as colunas novas precisam ser criadas manualmente no banco (Aiven).
ALTER TABLE users ADD COLUMN session_version INT NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';

-- Promover um usuário a administrador (trocar o email):
-- UPDATE users SET role = 'admin' WHERE email = 'admin@email.com';
