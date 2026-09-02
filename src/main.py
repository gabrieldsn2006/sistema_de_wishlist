# fastapi hello world example
import uvicorn, dotenv
from fastapi import FastAPI

env = dotenv.load_dotenv()
DB_HOST = env.get("DB_HOST")
DB_PORT = env.get("DB_PORT")
DB_USER = env.get("DB_USER")
DB_PASSWORD = env.get("DB_PASSWORD")

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.get("/users")
async def list_users():
    return {"users": []}

@app.post("/users")
async def create_user():
    return {"message": "User created"}

@app.get("/users/{id}")
async def get_user(id: int):
    return {"user": {"id": id}}

@app.put("/users/{id}")
async def update_user(id: int):
    return {"message": "User updated"}

@app.delete("/users/{id}")
async def delete_user(id: int):
    return {"message": "User deleted"}

@app.get("/games")
async def list_games():
    return {"games": []}

@app.post("/games")
async def create_game():
    return {"message": "Game created"}

@app.get("/games/{id}")
async def get_game(id: int):
    return {"game": {"id": id}}

@app.put("/games/{id}")
async def update_game(id: int):
    return {"message": "Game updated"}

@app.delete("/games/{id}")
async def delete_game(id: int):
    return {"message": "Game deleted"}

# Wishlist endpoints
@app.post("/wishlist")
async def add_to_wishlist():
    return {"message": "Game added to wishlist"}

@app.get("/wishlist/{user_id}")
async def list_wishlist(user_id: int):
    return {"games": []}

@app.delete("/wishlist/{id}")
async def remove_from_wishlist(id: int):
    return {"message": "Game removed from wishlist"}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
