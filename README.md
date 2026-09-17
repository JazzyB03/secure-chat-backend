# Secure Real-Time Chat Workspace

A production-ready, fully containerized real-time chat application built using an asynchronous Python backend, a secure JWT authorization gateway, and persistent PostgreSQL storage. 

** Live Demo Link:** [secure-chat-backend-production-fe14.up.railway.app]

---

## Application Architecture Overview
This system relies on persistent, full-duplex **WebSockets** for instant message delivery without browser polling or page refreshes.

*   **Asynchronous Processing:** Built using **FastAPI** and `asyncio` to manage thousands of active connection pipelines concurrently without blocking the server.
*   **Persistent Storage:** Integrated with **PostgreSQL** via the modern **SQLAlchemy 2.0 ORM** using the asynchronous `asyncpg` dialect.
*   **Security & Gatekeeping:** Implements password-protected chat rooms using **Bcrypt** cryptographic hashing and custom signed **JWT (JSON Web Tokens)** to authorize WebSocket upgrade handshakes.
*   **Containerized Orchestration:** Standardized via **Docker** and `docker-compose` to enforce identical environments across development, testing, and cloud deployment.

---

## Technology Stack
*   **Backend:** Python 3.11, FastAPI, Uvicorn, WebSockets
*   **Database & ORM:** PostgreSQL 15, SQLAlchemy 2.0, Asyncpg
*   **Security:** PyJWT, Bcrypt
*   **DevOps & Deployment:** Docker, Docker Compose, Git, Railway.app
*   **Frontend:** Vanilla JavaScript (Native HTML5 WebSocket API), CSS3 (Modern Dark-Mode Grid Layout)

---

## Features Implemented
*   **Dynamic Room Authentication:** Creating or joining a room checks credentials through a secure HTTP `POST` gateway. If the room is new, it salts and hashes the password via Bcrypt before saving it.
*   **Handshake Guard:** WebSockets reject unauthorized entry (Status Code 1008) if an invalid, expired, or tampered JWT access pass is detected in the query parameters.
*   **Historical Log Syncing:** Upon entering a validated room channel, the backend asynchronously fetches and delivers the last 50 room messages out of PostgreSQL so history is never lost on refresh.
*   **Dynamic UI State Tracking:** Live Javascript updates a connection status badge (Online/Offline) and handles automatic, smooth scrolling to incoming messages.
*   **UI/UX Quality-of-Life:** Hidden/Visible text toggles integrated natively into password fields to enhance user entry validation.

---

## Local Installation & Setup (Using Docker)

To run this application locally, ensure you have **Docker** and **Docker Compose** installed on your system.

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd secure-chat-app
   ```
   
2. **Spin up the application stack:**
   This command downloads the Postgres image, builds your custom Python app container, sets up internal network bridges, and launches the cluster:
   ```bash
   docker-compose up --build
   ```

3. **Initialize the Local Database Schema:**
   Open your browser and navigate to the database setup endpoint to trigger the SQLAlchemy structural generation scripts:
   ```text
   http://localhost:8000/init-db
   ```

4. **Start Chatting:**
   Navigate to the root URL to open the user interface. Open multiple browser tabs or separate devices on your local network to test real-time communication:
   ```text
   http://localhost:8000/
   ```

---

## Core API & Socket Specification

### 1. Room Verification & Token Minting
*   **Endpoint:** `POST /api/auth-room`
*   **Payload:**
    ```json
    {
      "username": "Alice",
      "room_id": "secure-lounge",
      "password": "password123"
    }
    ```
*   **Response:** `{"token": "JWT_STRING_GOES_HERE"}`

### 2. WebSocket Upgrade Pipeline
*   **Endpoint:** `WS /ws/{room_id}?token={JWT_STRING}`
*   **Description:** Establishes a persistent full-duplex socket channel if the signed JWT token payload matches the target room ID.

---

## Real-World Edge Cases Handled
*   **Database Container Race Conditions:** Built out a robust manual initializer utility path (`/init-db`) to prevent application container launch crashes caused by slow Postgres cloud boot protocols.
*   **Cloud Clock & Timezone Drifts:** Applied a 10-second validation `leeway` threshold cushion inside PyJWT token processing to prevent sudden browser/server timing desynchronization disconnects.
*   **Cross-Origin Compliance (CORS):** Implemented targeted fastapi middleware wrappers to properly fulfill cross-origin preflight requests across dynamic operating systems and browsers (Chrome Linux/Windows).
