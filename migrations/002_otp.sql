-- Campos do código de verificação por SMS (2FA)
ALTER TABLE users ADD COLUMN otp_hash VARCHAR(255) NULL;
ALTER TABLE users ADD COLUMN otp_expires_at DATETIME NULL;
ALTER TABLE users ADD COLUMN otp_attempts INT NOT NULL DEFAULT 0;
