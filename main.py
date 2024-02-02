from fastapi import FastAPI, Depends
from routers import auth, translate, game
from fastapi.encoders import jsonable_encoder
import os
import uvicorn

app = FastAPI()
app.include_router(auth.router)
app.include_router(translate.router)
app.include_router(game.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)