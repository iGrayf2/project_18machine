import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = {
                "type": "machine_status",
                "data": {
                    "recipes_count": 3,
                    "recipes": [
                        {"id": 1, "name": "Мочалка A"},
                        {"id": 2, "name": "Мочалка B"},
                        {"id": 3, "name": "Тест"},
                    ],
                    "selected_recipe_id": 1,
                    "recipe_repeats_target": 10,
                    "encoder_angle": 187,
                    "rpm": 42,
                    "current_cycle_index": 2,
                    "cycles_total": 5,
                    "current_cycle_turn": 7,
                    "current_cycle_turn_target": 20,
                    "current_recipe_repeat": 1,
                    "state": "running",
                },
            }

            await websocket.send_json(data)

            try:
                incoming = await asyncio.wait_for(websocket.receive_json(), timeout=0.2)
                print("WS action:", incoming)
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        print("WebSocket disconnected")