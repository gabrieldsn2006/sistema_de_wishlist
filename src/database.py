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

configured_ca = os.getenv("DB_SSL_CA", "ca.pem")
DB_SSL_CA = Path(configured_ca)
if not DB_SSL_CA.is_absolute():
    DB_SSL_CA = PROJECT_ROOT / DB_SSL_CA

if not DB_SSL_CA.is_file():
    raise FileNotFoundError(f"Certificado CA não encontrado: {DB_SSL_CA}")

DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl": {"ca": str(DB_SSL_CA)}},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
