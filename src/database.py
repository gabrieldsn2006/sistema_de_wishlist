import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "wishlist")



def build_engine():
    # DATABASE_URL (opcional) troca o MySQL por outro banco, ex.: sqlite:///wishlist.db para testes locais
    override = os.getenv("DATABASE_URL")
    if override:
        connect_args = {"check_same_thread": False} if override.startswith("sqlite") else {}
        return create_engine(override, connect_args=connect_args, pool_pre_ping=True)

    ca_path = Path(os.getenv("DB_SSL_CA", "ca.pem"))
    if not ca_path.is_absolute():
        ca_path = PROJECT_ROOT / ca_path
    if not ca_path.is_file():
        raise FileNotFoundError(f"Certificado CA não encontrado: {ca_path}")

    url = URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
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
