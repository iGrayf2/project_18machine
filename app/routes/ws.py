import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.execution_service import execution_service

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    async def sender_loop():
        while True:
            snapshot = execution_service.get_status_snapshot()

            await websocket.send_json({
                "type": "machine_status",
                "data": snapshot,
            })

            await asyncio.sleep(0.1)

    async def receiver_loop():
        while True:
            payload = await websocket.receive_json()
            response = execution_service.handle_action(payload)
            if response:
                await websocket.send_json(response)

    sender_task = asyncio.create_task(sender_loop())
    receiver_task = asyncio.create_task(receiver_loop())

    try:
        done, pending = await asyncio.wait(
            [sender_task, receiver_task],
            return_when=asyncio.FIRST_EXCEPTION,
        )

        for task in pending:
            task.cancel()

        for task in done:
            exc = task.exception()
            if exc:
                raise exc

    except WebSocketDisconnect:
        print("WebSocket disconnected")

    except Exception as e:
        print(f"WebSocket error: {e}")

    finally:
        sender_task.cancel()
        receiver_task.cancel()