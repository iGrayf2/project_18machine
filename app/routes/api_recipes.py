from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.routes.ws import execution_service

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


class RecipesPayload(BaseModel):
    recipes: list[dict]


@router.get("")
async def get_recipes():
    return {
        "recipes": execution_service.recipe_service.get_all_recipes()
    }


@router.post("/save")
async def save_recipes(payload: RecipesPayload):
    recipes = payload.recipes

    if not recipes:
        raise HTTPException(status_code=400, detail="Список рецептов пуст")

    execution_service.recipe_service.replace_all_recipes(recipes)

    current_recipe = execution_service.recipe_service.get_first_recipe()
    if current_recipe:
        execution_service.hardware.reset_all_valves()
        execution_service.engine.load_recipe(current_recipe)

    return {"ok": True}