import uvicorn
from fastapi import FastAPI

import models
from database import Base, engine
from routers import alerts, auth, games, users, wishlist

# Cria as tabelas no banco caso ainda não existam
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Wishlist de Jogos",
    description="API REST para gerenciar usuários, jogos e a wishlist de cada usuário. "
    "Integra com o Serviço de Preços (REST) e recebe dele os avisos de queda de preço (webhook).",
    version="2.0.0",
)


@app.get("/")
async def read_root():
    return {"message": "Wishlist API no ar"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(games.router)
app.include_router(wishlist.router)
app.include_router(alerts.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
