import jwt
import bcrypt
from datetime import datetime, timedelta, UTC

SECRET_KEY = "this-secret-key-will-change-later"
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Generates a short-lived JWT token authorizing access to a room."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_room_token(username: str, room_id: str) -> str:
    """Generates a short-lived JWT token authorizing access to a room."""
    expire = datetime.now(UTC) + timedelta(minutes=15)
    payload = {
        "sub": username,
        "room_id": room_id,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_room_token(token: str) -> dict:
    """Decodes and validates a JWT token. Returns payload or None if invalid."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None