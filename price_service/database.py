import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SERVICE_ROOT = Path(__file__).resolve().parent
# Só o .env desta pasta: o .env da raiz é da Wishlist API (DB_NAME=wishlist)
load_dotenv(SERVICE_ROOT / ".env")


def build_engine():
    # DATABASE_URL (opcional) troca o MySQL por outro banco, ex.: sqlite:///prices.db para testes locais
    override = os.getenv("DATABASE_URL")
    if override:
        connect_args = {"check_same_thread": False} if override.startswith("sqlite") else {}
        return create_engine(override, connect_args=connect_args, pool_pre_ping=True)

    ca_path = Path(os.getenv("DB_SSL_CA", "ca.pem"))
    if not ca_path.is_absolute():
        ca_path = SERVICE_ROOT / ca_path
    if not ca_path.is_file():
        raise FileNotFoundError(f"Certificado CA não encontrado: {ca_path}")

    # Mesma instância MySQL da Aiven, mas outro banco (o padrão é "prices")
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "prices"),
    )
    return create_engine(url, connect_args={"ssl": {"ca": str(ca_path)}}, pool_pre_ping=True)


engine = build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
