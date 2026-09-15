from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, UTC
from src.database import Base

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(String, primary_key=True, index=True) # The room name/ID
    hashed_password = Column(String, nullable=False)

    def __init__(self, id: str, hashed_password: str):
        self.id = id
        self.hashed_password = hashed_password
    
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String, index=True, nullable=False)
    username = Column(String, nullable=False)
    message = Column(String, nullable=False)
    # Store timestamp using uniform UTC timing rules. 09/11/26 add timezone=true to fix conflict with sqlalchemy
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Explicit constructor mapping fields we control
    def __init__(self, room_id: str, username: str, message: str):
        self.room_id = room_id
        self.username = username
        self.message = message