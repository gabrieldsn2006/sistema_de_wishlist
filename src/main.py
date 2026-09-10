import uvicorn
from fastapi import FastAPI

import models
from database import Base, engine
from routers import games, users, wishlist

# Cria as tabelas no banco caso ainda não existam
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Wishlist de Jogos",
    description="API REST para gerenciar usuários, jogos e a wishlist de cada usuário.",
    version="1.0.0",
)


@app.get("/")
async def read_root():
    return {"message": "Wishlist API no ar"}


app.include_router(users.router)
app.include_router(games.router)
app.include_router(wishlist.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
