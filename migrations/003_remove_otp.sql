-- Opcional: remove as colunas do código por SMS, que saiu na AV3.
-- Deixá-las no banco não quebra nada (o código não usa mais).
ALTER TABLE users DROP COLUMN otp_hash;
ALTER TABLE users DROP COLUMN otp_expires_at;
ALTER TABLE users DROP COLUMN otp_attempts;

-- A tabela "alerts" é nova e é criada sozinha pelo SQLAlchemy (create_all) na subida da API.
