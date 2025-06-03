# Tutorial: Building a Scalable Background Task Processing System with WebSockets, Celery, Redis, and FastAPI

## Objectives
In this tutorial, you will:
1. Learn how to implement WebSocket integration in FastAPI for real-time task updates.
2. Utilize Celery and Redis for task management and message brokering.
3. Set up Docker to containerize the application and make it scalable.
4. Integrate Celery workers and learn how to scale them horizontally.

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

**Description of Code Snippet:**
- Initializes a **FastAPI** app and sets up a **WebSocket** endpoint for real-time communication.
- Manages WebSocket connections using the `ConnectionManager` class.
- Uses Redis pub/sub to listen for updates from Celery tasks and broadcasts them via WebSockets.
- Exposes HTTP routes to start tasks and fetch task statuses.

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

**Description of Code Snippet:**
- Defines a **Celery task** named `create_task` that simulates a long-running task.
- Publishes task progress updates to Redis, which are later broadcast to WebSocket clients.
- Uses the `update_state` method to track task progress.

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

**Description of Code Snippet:**
- Defines a **Docker image** for the application using the slim version of Python 3.11.
- Installs dependencies from `requirements.txt` and copies the application code into the container.
- Runs the FastAPI application using Uvicorn.

---

### 2. Create `docker-compose.yml`

```yaml name=docker-compose.yml
version: '3.8'

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

**Description of Code Snippet:**
- Configures **Docker Compose** to orchestrate the `web`, `redis`, and `worker` services.
- The `web` service runs the FastAPI app.
- The `worker` service runs Celery workers for background task processing.
- The `redis` service acts as the message broker.

---

### 3. Create `requirements.txt`

```text name=requirements.txt
fastapi
uvicorn
celery
redis
jinja2
```

**Description of Code Snippet:**
- Lists the Python dependencies required for the application, including FastAPI, Celery, Redis, and Jinja2 for templating.

---

## Scaling Celery Workers

Scale Celery workers using Docker Compose:

```bash
docker-compose up --scale worker=3
```

**Description:**
- This command launches 3 instances of the `worker` service to handle tasks concurrently.

---

## Testing the Application

### Start the Application
Run the application using:
```bash
docker-compose up --build
```

**Description:**
- Builds the Docker images and starts the services defined in `docker-compose.yml`.

---

### Access the Web Interface
Open your browser and go to:
```
http://localhost:8000
```

**Description:**
- Access the FastAPI web interface to interact with the application.

---

### Test WebSocket Integration
1. Open the developer console in your browser.
2. Go to the "Network" tab and filter for "WS" (WebSocket).
3. Start a task and observe WebSocket messages in real time.

**Description:**
- Verify that the WebSocket connection is established and receiving real-time updates for task progress.

---

## Next Steps

In the next tutorial, we will cover:
- Deploying this application to AWS EC2.
- Setting up auto-scaling for Celery workers in the cloud.
- Monitoring task performance and Redis metrics.
