from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.ui import router as ui_router
from app.routes.ws import router as ws_router
from app.routes.api_recipes import router as api_recipes_router
from app.services.execution_service import execution_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    try:
        execution_service.close()
        print("[APP] Execution service closed")
    except Exception as e:
        print(f"[APP] Shutdown error: {e}")


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(ui_router)
app.include_router(ws_router)
app.include_router(api_recipes_router)