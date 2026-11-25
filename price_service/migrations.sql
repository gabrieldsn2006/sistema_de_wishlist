-- Banco do Serviço de Preços: rodar uma vez na mesma instância MySQL da Aiven.
-- As tabelas (tracked_games, price_history, webhook_outbox) são criadas sozinhas
-- pelo SQLAlchemy (create_all) na primeira subida do serviço.
CREATE DATABASE IF NOT EXISTS prices;
