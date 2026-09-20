from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import uuid

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        # game_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)

    def disconnect(self, websocket: WebSocket, game_id: str):
        if game_id in self.active_connections:
            self.active_connections[game_id].remove(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

    async def broadcast(self, message: dict, game_id: str):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                await connection.send_json(message)


manager = ConnectionManager()


@app.get("/")
def read_root():
    return {"message": "Monopoly Server is running"}


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await manager.connect(websocket, game_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Process game action here later
            message = json.loads(data)
            print(f"Received from {game_id}: {message}")
            
            # Echo back for now
            await manager.broadcast({"type": "ECHO", "data": message}, game_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
        await manager.broadcast({"type": "INFO", "message": "A player left the game"}, game_id)
