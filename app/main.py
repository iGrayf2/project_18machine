from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.ui import router as ui_router
from app.routes.ws import router as ws_router
from app.routes.api_recipes import router as api_recipes_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(ui_router)
app.include_router(ws_router)
app.include_router(api_recipes_router)