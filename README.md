# Tutorial: Building a Scalable Background Task Processing System with WebSockets, Celery, Redis, and FastAPI

## Objectives
In this tutorial, we will:
1. Learn how to implement WebSocket integration in FastAPI for real-time task updates.
2. Utilize Celery and Redis for task management and message brokering.
3. Set up Docker to containerize the application and make it scalable.
4. Integrate Celery workers and learn how to scale them horizontally.

---

## Introduction

Modern applications often require background task processing for handling long-running or resource-intensive operations, such as file processing, sending emails, or generating reports. This tutorial guides you step-by-step to build a FastAPI application that uses:
- **WebSockets** for real-time updates.
- **Celery** for background task processing.
- **Redis** as the message broker.
- **Docker Compose** for containerized deployment.

By the end of this tutorial, you will have a fully functional application running in Docker that can scale to handle multiple tasks concurrently.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Setting Up the Project](#setting-up-the-project)
3. [Implementing the Application](#implementing-the-application)
    - [FastAPI WebSocket Integration](#fastapi-websocket-integration)
    - [Celery Task Processing](#celery-task-processing)
4. [Setting Up Docker](#setting-up-docker)
5. [Scaling Celery Workers](#scaling-celery-workers)
6. [Testing the Application](#testing-the-application)

---

## System Architecture

### Overview

The application consists of:
1. **FastAPI**: Handles HTTP requests and WebSocket connections.
2. **Redis**: Acts as a message broker and pub/sub system for real-time updates.
3. **Celery**: Processes background tasks.
4. **Docker Compose**: Orchestrates the application components.

### Workflow

1. The client sends a request to create a background task.
2. FastAPI creates the task and returns a `task_id`.
3. Celery workers execute the task and publish progress updates to Redis.
4. FastAPI listens to Redis and broadcasts updates to clients via WebSockets.
5. The client receives real-time updates about task progress.

---

## Setting Up the Project

### Directory Structure

The project will have the following structure:
```
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── celery_worker.py
│   ├── templates/
│   │   └── index.html
│   ├── static/
│       └── css/
│           └── styles.css
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
```

---

## Implementing the Application

### 1. FastAPI WebSocket Integration

#### File: `app/main.py`

```python name=app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import redis
import asyncio
import logging
import os
from app.celery_worker import create_task

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(title="Background Task Example")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Redis configuration
redis_host = os.getenv("REDIS_HOST", "redis")
redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)
pubsub = redis_client.pubsub()
pubsub.subscribe("task_status")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Redis listener to publish updates via WebSockets
async def redis_listener():
    async def listen():
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                data = message.get("data")
                if data:
                    await manager.broadcast(data)
            await asyncio.sleep(0.01)

    asyncio.create_task(listen())

@app.on_event("startup")
async def startup_event():
    await redis_listener()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/tasks")
async def add_task(background_tasks: BackgroundTasks):
    task = create_task.delay(10)
    return {"task_id": task.id, "status": "Task started"}

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = create_task.AsyncResult(task_id)
    return {"task_id": task_id, "status": task.status, "result": task.result}
```

---

### 2. Celery Task Processing

#### File: `app/celery_worker.py`

```python name=app/celery_worker.py
from celery import Celery
import time
import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
celery = Celery("tasks", broker=f"redis://{REDIS_HOST}:6379/0", backend=f"redis://{REDIS_HOST}:6379/0")

redis_client = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

@celery.task(name="create_task", bind=True)
def create_task(self, task_length):
    for i in range(task_length):
        progress = int((i + 1) * 100 / task_length)
        self.update_state(state="PROGRESS", meta={"progress": progress})
        redis_client.publish("task_status", json.dumps({"task_id": self.request.id, "progress": progress}))
        time.sleep(1)
    return {"status": "Task completed"}
```

---

## Setting Up Docker

### 1. Create `Dockerfile`

```dockerfile name=Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Create `docker-compose.yml`

```yaml name=docker-compose.yml

services:
  web:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - worker

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  worker:
    build: .
    command: celery -A app.celery_worker worker --loglevel=info
    depends_on:
      - redis
```

### 3. Create `requirements.txt`

```text name=requirements.txt
fastapi
uvicorn
celery
redis
jinja2
```

---

## Scaling Celery Workers

Scale Celery workers using Docker Compose:

```bash
docker-compose up --scale worker=3
```

---

## Testing the Application

### Start the Application
Run the application using:
```bash
docker-compose up --build
```

### Access the Web Interface
Open your browser and go to:
```
http://localhost:8000
```

### Test WebSocket Integration
1. Open the developer console in your browser.
2. Go to the "Network" tab and filter for "WS" (WebSocket).
3. Start a task and observe WebSocket messages in real time.

---

## Next Steps

In the next tutorial, we will cover:
- Deploying this application to AWS EC2.
- Setting up auto-scaling for Celery workers in the cloud.
- Monitoring task performance and Redis metrics.
