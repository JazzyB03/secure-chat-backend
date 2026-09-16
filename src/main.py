import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from src.database import engine, Base, AsyncSessionLocal
from src.models import ChatMessage, ChatRoom
from src.auth import hash_password, verify_password, create_room_token, decode_room_token
from sqlalchemy import select
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 [STARTUP] Secure Chat Engine booted up instantly!", flush=True)
    yield
    print("😴 [SHUTDOWN] Clean shutdown complete.", flush=True)

app = FastAPI(title="Real-Time Chat Backend", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRoomManager:
    def __init__(self):
        self.active_rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
        self.active_rooms[room_id].append(websocket)

        # Pull past chat logs for the freshly joined user channel
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ChatMessage)
                    .where(ChatMessage.room_id == room_id)
                    .order_by(ChatMessage.timestamp.asc())
                    .limit(50)
                )
                for msg in result.scalars().all():
                    await websocket.send_text(f"{msg.username}: {msg.message}")
        except Exception as e:
            print(f"⚠️ History lookup bypassed: {e}", flush=True)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_rooms and websocket in self.active_rooms[room_id]:
            self.active_rooms[room_id].remove(websocket)

    async def broadcast_to_room(self, message: str, room_id: str):
        if room_id in self.active_rooms:
            for connection in self.active_rooms[room_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass

manager = ChatRoomManager()

# Data Validation Layout for Pydantic
class AuthRequest(BaseModel):
    username: str
    room_id: str
    password: str

# Room Entry & Generation Authentication Endpoint
@app.post("/api/auth-room")
async def auth_room(data: AuthRequest):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ChatRoom).where(ChatRoom.id == data.room_id))
        room = result.scalar_one_or_none()

        if not room:
            new_room = ChatRoom(id=data.room_id, hashed_password=hash_password(data.password))
            session.add(new_room)
            await session.commit()
            print(f"🔑 Created password-protected room rows: {data.room_id}", flush=True)
        else:
            if not verify_password(data.password, room.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid password for this room.")

    token = create_room_token(username=data.username, room_id=data.room_id)
    return {"token": token}

# Schema Table Initalizer Route
@app.get("/init-db")
async def initialize_database():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return {"status": "success", "message": "Database tables built/verified successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database build failed: {str(e)}")

# Root Web Interface Server Engine
@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r") as file:
        return file.read()

# WebSocket Stream Router Channel
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str = Query(...)):
    payload = decode_room_token(token)
    if not payload or payload.get("room_id") != room_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            
            if "]: " in data:
                raw_user, raw_msg = data.split("]: ", 1)
                clean_user = raw_user.replace("[", "")
            else:
                clean_user = payload.get("sub", "Anonymous")
                raw_msg = data

            try:
                async with AsyncSessionLocal() as session:
                    db_msg = ChatMessage(room_id=room_id, username=clean_user, message=raw_msg)
                    session.add(db_msg)
                    await session.commit()
            except Exception as e:
                print(f"⚠️ Database live record write failure: {e}", flush=True)

            await manager.broadcast_to_room(data, room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast_to_room(f"⚠️ {payload.get('sub')} has left the chat room.", room_id)