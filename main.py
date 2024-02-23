import sys
sys.path.append("..")
import starlette.status as status

from fastapi import FastAPI, responses
from routers import auth, translate, game, home
from starlette.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(home.router)
app.include_router(auth.router)
app.include_router(translate.router)
app.include_router(game.router)

@app.get("/")
async def redirect():
    return responses.RedirectResponse(
        '/home', 
        status_code=status.HTTP_302_FOUND)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)