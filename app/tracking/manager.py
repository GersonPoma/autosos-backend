from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[int, list[WebSocket]] = {}

    async def connect(self, incidente_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms.setdefault(incidente_id, []).append(websocket)

    def disconnect(self, incidente_id: int, websocket: WebSocket) -> None:
        room = self.rooms.get(incidente_id, [])
        if websocket in room:
            room.remove(websocket)
        if not room:
            self.rooms.pop(incidente_id, None)

    async def broadcast(self, incidente_id: int, mensaje: dict) -> None:
        room = list(self.rooms.get(incidente_id, []))
        dead: list[WebSocket] = []
        for ws in room:
            try:
                await ws.send_json(mensaje)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(incidente_id, ws)


manager = ConnectionManager()