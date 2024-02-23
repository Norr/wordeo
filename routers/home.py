
import sys
from fastapi.templating import Jinja2Templates

sys.path.append("..")

from starlette import status
from fastapi.responses import HTMLResponse
from fastapi import APIRouter,  Request
from starlette import status
from starlette.responses import RedirectResponse
from .auth import get_current_user
from database.db_connection import Database

templates = Jinja2Templates(directory="templates")

router = APIRouter(
    prefix="/home",
    tags=["home"],
    responses={401: {"user": "Not authorized"}})


def get_db():
    try:
        eng = Database()._get_engine()
        yield eng
    finally:
        ...

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = await get_current_user(request)
    if user is None or user == "Session expired":
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("home.html", {"request": request, "user": user})
