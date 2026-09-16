import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Dict
import os


# Database imports
from src.database import engine, Base, AsyncSessionLocal
from src.models import ChatMessage, ChatRoom
from src.auth import hash_password, verify_password, create_room_token, decode_room_token
from sqlalchemy import select
from pydantic import BaseModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This block executes BEFORE the server starts accepting web traffic
    # Retry loop to wait for PostgreSQL to fully boot up
    retries = 5
    while retries > 0:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database Tables successfully verified/created!")
            break  # Exit loop on success
        except Exception as e:
            retries -= 1
            print(f"⚠️ Database not ready yet ({retries} retries left)... Waiting 2 seconds.")
            await asyncio.sleep(2)
            if retries == 0:
                print(f"❌ DATABASE STARTUP CRITICAL ERROR: {e}")
    
    yield  # Hand over control to FastAPI to start serving web traffic
    
    # Optional, probably do later: Put any database shutdown/cleanup code here if needed
    print("😴 Shutting down application...")

# Currently will pass the lifespan context directly into FastAPI
app = FastAPI(title="Real-Time Chat Backend", lifespan=lifespan)

origins = [
    "http://localhost:8000", 
    "http://127.0.0.1:8000",
    "secure-chat-backend-production-ddf2.up.railway.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allows traffic from any public web browser address link
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, OPTIONS, etc.
    allow_headers=["*"],
)

class ChatRoomManager:
    def __init__(self):
        #Dictionary mapping room IDs to a list of active WebSocket connections
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id:str):
        """Accepts a connection and stores it in the specified room."""
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []
        self.active_rooms[room_id].append(websocket)

        # FETCH HISTORY: Grab the last 50 messages for this specific room
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ChatMessage)
                    .where(ChatMessage.room_id == room_id)
                    .order_by(ChatMessage.timestamp.asc())
                    .limit(50)
                )
                messages = result.scalars().all()
                for msg in messages:
                    await websocket.send_text(f"{msg.username}: {msg.message}")
        except Exception as e:
            print(f"⚠️ Failed to fetch history log: {e}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_rooms:
            self.active_rooms[room_id].remove(websocket)
            if not self.active_rooms[room_id]:
                del self.active_rooms[room_id]

    async def broadcast_to_room(self, message: str, room_id: str):
        """Sends a text message to every active connection inside a specific room."""
        if room_id in self.active_rooms:
            for connection in self.active_rooms[room_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    # Catch and ignore stale connections that haven't registered as disconnected yet
                    pass
                
manager = ChatRoomManager()

# Data Validation Layout for room joins 
class AuthRequest(BaseModel):
    username: str
    room_id: str
    password: str

@app.post("/api/auth-room")
async def auth_room(data: AuthRequest):
    async with AsyncSessionLocal() as session:
        # 1. Look up if the room exists
        result = await session.execute(select(ChatRoom).where(ChatRoom.id == data.room_id))
        room = result.scalar_one_or_none()

        if not room:
            # 2. Room doesn't exist, create it cleanly
            new_room = ChatRoom(id=data.room_id, hashed_password=hash_password(data.password))
            session.add(new_room)
            
            # Explicitly commit changes safely without double-nesting transactions
            await session.commit()
            print(f"🔑 Created new password-protected room: {data.room_id}")
        else:
            # 3. Room exists, verify the password
            if not verify_password(data.password, room.hashed_password):
                raise HTTPException(status_code=401, detail="Invalid password for this room.")

    # 4. Issue token upon verification success
    token = create_room_token(username=data.username, room_id=data.room_id)
    return {"token": token}    

@app.get("/", response_class=HTMLResponse)
def read_root():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(template_path, "r") as file:
        return file.read()

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str = Query(...)):
    # SECURITY STEP: Decode and inspect JWT token validity
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
                clean_user = "Anonymous"
                raw_msg = data

            # SAVE TO DB: Open session asynchronously
            try:
                async with AsyncSessionLocal() as session:
                    db_msg = ChatMessage(room_id=room_id, username=clean_user, message=raw_msg)
                    session.add(db_msg)
                    await session.commit()
            except Exception as e:
                print(f"⚠️ Database write failed live: {e}")

            await manager.broadcast_to_room(data, room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        await manager.broadcast_to_room("⚠️ A user has left the chat room.", room_id)