# Tutorial: Building a Scalable Background Task Processing System with WebSockets, Celery, Redis, and FastAPI

## Objectives
In this tutorial, we will:
1. Learn how to implement WebSocket integration in FastAPI for real-time task updates.
2. Utilize Celery and Redis for task management and message brokering.
3. Set up Docker to containerize the application and make it scalable.
4. Integrate Celery workers and learn how to scale them horizontally.

---
---

## Introduction

Modern applications often require background task processing for handling long-running or resource-intensive operations, such as file processing, sending emails, or generating reports. This tutorial guides you step-by-step to build a FastAPI application that uses:
- **WebSockets** for real-time updates.
- **Celery** for background task processing.
- **Redis** as the message broker.
- **Docker Compose** for containerized deployment.

By the end of this tutorial, you will have a fully functional application running in Docker that can scale to handle multiple tasks concurrently.

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

### Combining Docker Architecture with Scaling and WebSocket Workflow
```mermaid
%%{init: {'theme': 'default', 'themeVariables': {'primaryColor': '#ffcc00', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#f0f0f0'}}}%%
%%{config: {'flowchart': {'curve': 'linear'}}}%%
%%{flowchart: {'nodeSpacing': 50, 'rankSpacing': 50}}%%
%%{flowchart: {'defaultRenderer': 'dagre'}}%%
graph TD
    subgraph "Docker Environment"
        A["Web Container (FastAPI)"] -->|"Publishes Tasks"| B["Redis Container (Broker)"]
        B -->|"Assign Tasks"| C["Worker 1"]
        B -->|"Assign Tasks"| D["Worker 2"]
        B -->|"Assign Tasks"| E["Worker ...N"]
        C -->|"Sends Progress"| B
        D -->|"Sends Progress"| B
        E -->|"Sends Progress"| B
        B -->|"Publishes Updates"| A
    end
    Client -->|"HTTP Request (Start Task)"| A
    A -->|"WebSocket Updates"| Client
    
    %% Style nodes with colors related to their technology icons
    style A fill:#009688,stroke:#007566,color:white,stroke-width:2px %% FastAPI teal color
    style B fill:#DC382D,stroke:#a9291f,color:white,stroke-width:2px %% Redis red color
    style C fill:#4e9e40,stroke:#3b7830,color:white,stroke-width:2px %% Celery worker green color
    style D fill:#4e9e40,stroke:#3b7830,color:white,stroke-width:2px %% Celery worker green color
    style E fill:#4e9e40,stroke:#3b7830,color:white,stroke-width:2px %% Celery worker green color
    style Client fill:#4285F4,stroke:#3367d6,color:white,stroke-width:2px %% Browser blue color
```

### Visualizing Docker Container Architecture and Connections
```mermaid
%%{init: {'theme': 'default', 'themeVariables': {'primaryColor': '#ffcc00', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#f0f0f0'}}}%%
%%{config: {'flowchart': {'curve': 'cardinal', 'padding': 20}}}%%
%%{flowchart: {'nodeSpacing': 80, 'rankSpacing': 120}}%%
%%{flowchart: {'defaultRenderer': 'dagre'}}%%

graph TD
    subgraph Docker["🐳 Docker Environment"]
        A["Web Container<br/>(FastAPI Server)"] 
        B["Redis Container<br/>(Message Broker)"]
        C["Worker Container<br/>(Celery Worker)"]
    end
    
    Client["📱 Client<br/>(Browser/App)"]

    %% Bold contrasting arrows
    A ==>|"Publishes Tasks"| B
    B ==>|"Sends Task to Process"| C
    C -.->|"Publishes Progress"| B
    B -.->|"Updates via Pub/Sub"| A
    
    %% Client interactions
    Client ==>|"HTTP Request"| A
    A -.->|"🔄 WebSocket Updates"| Client

    %% Enhanced styling
    classDef fastApiStyle fill:#009688,stroke:#007566,color:white,stroke-width:3px
    classDef redisStyle fill:#DC382D,stroke:#a9291f,color:white,stroke-width:3px
    classDef celeryStyle fill:#4e9e40,stroke:#3b7830,color:white,stroke-width:3px
    classDef clientStyle fill:#4285F4,stroke:#3367d6,color:white,stroke-width:3px
    classDef dockerStyle fill:#E6F3FF,stroke:#2496ED,color:#333,stroke-width:2px,fill-opacity:0.3

    %% Apply styles
    class A fastApiStyle
    class B redisStyle
    class C celeryStyle
    class Client clientStyle
    class Docker dockerStyle

    %% Bold contrasting arrow styles
    linkStyle 0 stroke:#FF0000,stroke-width:3px
    linkStyle 1 stroke:#FF6600,stroke-width:3px
    linkStyle 2 stroke:#0066FF,stroke-width:2px,stroke-dasharray: 8 4
    linkStyle 3 stroke:#9900FF,stroke-width:2px,stroke-dasharray: 8 4
    linkStyle 4 stroke:#00CC00,stroke-width:3px
    linkStyle 5 stroke:#FF3366,stroke-width:2px,stroke-dasharray: 8 4
```

### Visualizing Celery Worker Scaling
```mermaid
%%{init: {'theme': 'default', 'themeVariables': {'primaryColor': '#4285f4', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#1a73e8', 'lineColor': '#34a853', 'sectionBkgColor': '#f8f9fa', 'altSectionBkgColor': '#e8f0fe', 'gridColor': '#dadce0', 'tertiaryColor': '#fbbc04', 'background': '#ffffff', 'secondaryColor': '#ea4335', 'fontFamily': 'Arial, sans-serif'}}}%%
%%{config: {'flowchart': {'curve': 'basis', 'padding': 20}}}%%
%%{flowchart: {'nodeSpacing': 80, 'rankSpacing': 100}}%%

graph TD
    subgraph Redis["🔄 Redis Broker"]
        A["📋 Task Queue<br/>Central Message Hub"]
    end
    
    subgraph Workers["⚙️ Worker Pool"]
        B["🔨 Worker 1<br/>Processing Tasks"]
        C["🔨 Worker 2<br/>Processing Tasks"] 
        D["🔨 Worker N<br/>Processing Tasks"]
    end
    
    subgraph Web["🌐 Web Layer"]
        E["🚀 FastAPI Server<br/>REST & WebSocket"]
    end
    
    subgraph Client["👤 Client Side"]
        F["📱 Browser/App<br/>Real-time Updates"]
    end

    %% Task flow
    E -->|"📤 Publish Tasks"| A
    A -->|"⚡ Assign"| B
    A -->|"⚡ Assign"| C  
    A -->|"⚡ Assign"| D
    
    %% Progress updates
    B -->|"📊 Progress Updates"| A
    C -->|"📊 Progress Updates"| A
    D -->|"📊 Progress Updates"| A
    
    %% Client communication
    A -->|"📢 Status Updates"| E
    E -.->|"🔄 WebSocket Stream"| F

    %% Styling
    classDef redisStyle fill:#ff6b6b,stroke:#d63031,stroke-width:3px,color:#fff
    classDef workerStyle fill:#74b9ff,stroke:#0984e3,stroke-width:2px,color:#fff
    classDef webStyle fill:#55a3ff,stroke:#2d3436,stroke-width:3px,color:#fff
    classDef clientStyle fill:#fd79a8,stroke:#e84393,stroke-width:2px,color:#fff

    class A redisStyle
    class B,C,D workerStyle
    class E webStyle
    class F clientStyle
```
### WebSockets vs HTTP Polling for Task Updates
```mermaid
%%{init: {'theme': 'default', 'themeVariables': {'primaryColor': '#4285f4', 'primaryTextColor': '#ffffff', 'primaryBorderColor': '#1a73e8', 'lineColor': '#34a853', 'sectionBkgColor': '#f8f9fa', 'altSectionBkgColor': '#e8f0fe', 'gridColor': '#dadce0', 'tertiaryColor': '#fbbc04', 'background': '#ffffff', 'secondaryColor': '#ea4335', 'fontFamily': 'Arial, sans-serif', 'activationBorderColor': '#ff6b6b', 'activationBkgColor': '#ffe6e6'}}}%%

sequenceDiagram
    autonumber
    participant C as 📱 Client
    participant WS as 🚀 WebServer
    participant R as 🔄 Redis
    participant W as 🔨 Worker

    Note over C,W: 🔄 **HTTP Polling Approach** 🔄
    
    rect rgb(255, 245, 245)
        C->>+WS: 📤 POST /tasks
        WS->>+R: 📋 Publish Task ➡️
        R->>+W: ⚡ Assign Task
        W-->>-R: 📊 Progress Update ↗️
        R-->>-WS: ✅ Task Created
        WS-->>-C: 🆔 Task ID Response
        
        loop 🔄 Continuous Polling (Every 2-5s)
            C->>+WS: 🔍 GET /tasks/{task_id}
            WS->>+R: 📊 Get Progress
            R-->>-WS: 📈 Progress Data
            WS-->>-C: 📋 Response with Progress
            Note right of C: ⏱️ Wait 2-5 seconds
        end
    end

    Note over C,W: ⚡ **WebSocket Real-time Approach** ⚡
    
    rect rgb(240, 255, 245)
        C->>+WS: 🔌 WebSocket Connection
        WS-->>-C: ✅ Connection Established
        
        C->>+WS: 📤 POST /tasks
        WS->>+R: 📋 Publish Task ➡️
        R->>+W: ⚡ Assign Task
        WS-->>C: 🆔 Task ID Response
        
        loop 🚀 Real-time Updates (Instant)
            W-->>R: 📊 Progress Update ↗️
            R-->>WS: 📢 Publish Progress Event 🚀
            WS-->>C: 📡 WebSocket Message (Instant)
        end
        
        W-->>R: ✅ Task Completed
        R-->>WS: 🎉 Completion Event
        WS-->>C: ✅ Task Complete Notification
    end

    Note over C,W: 📊 **Comparison Summary** 📊
    Note over C,WS: 🔄 Polling: Multiple requests, delay<br/>⚡ WebSocket: Single connection, instant
```
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
│     
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
import json
import redis
from app.celery_worker import create_task  # Fixed import path
import logging
import os
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Background Task Example")

# Setup templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Redis connection
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
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

# Redis listener task
async def redis_listener():
    async def listen():
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                logger.info(f"Received message from Redis: {message}")
                try:
                    data = message.get("data")
                    if data:
                        await manager.broadcast(data)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")
            await asyncio.sleep(0.01)
    
    # Start the listener in the background
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
            data = await websocket.receive_text()
            # Process received data if needed
            logger.info(f"Received WebSocket data: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/tasks")
async def add_task(background_tasks: BackgroundTasks):
    # Create a Celery task
    task = create_task.delay(60)  # Example: 60 seconds task
    return {"task_id": task.id, "status": "Task started"}

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = create_task.AsyncResult(task_id)
    response = {
        "task_id": task_id,
        "status": task.status,
        "result": task.result
    }
    return response
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
import os
import time
import redis
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
BACKEND_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

celery = Celery('tasks',
                broker=BROKER_URL,
                backend=BACKEND_URL)

# Enhanced Celery configuration for better Flower integration
celery.conf.update(
    result_expires=3600,  # Results will expire after 1 hour
    task_track_started=True,  # Track when tasks are started
    task_time_limit=60 * 5,  # Tasks have 5 minutes to run
    worker_max_tasks_per_child=200,  # Worker processes will be recycled after 200 tasks
    worker_prefetch_multiplier=4,  # Number of tasks to prefetch per worker process
    worker_send_task_events=True,  # Send task-related events for Flower
    task_send_sent_event=True,  # Required for monitoring task execution
    event_queue_expires=60,  # Event queue expiry time in seconds
    worker_pool_restarts=True,  # Enable worker pool restarts
)

# Redis configuration for publishing status updates
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

@celery.task(name="create_task", bind=True)
def create_task(self, task_length):
    """
    Example background task that runs for a specified amount of time and updates
    progress through Redis pub/sub
    """
    logger.info(f"Task {self.request.id} started, running for {task_length} seconds")
    
    total_steps = task_length
    for step in range(total_steps):
        # Update progress
        percentage = int((step + 1) * 100 / total_steps)
        self.update_state(state="PROGRESS", meta={"progress": percentage})
        
        # Publish progress to Redis
        status_data = {
            "task_id": self.request.id,
            "status": "PROGRESS",
            "progress": percentage
        }
        redis_client.publish("task_status", json.dumps(status_data))
        
        # Simulate work with sleep
        time.sleep(1)
    
    # Final update
    result = {"status": "Task completed!", "result": 100}
    
    # Publish completion to Redis
    status_data = {
        "task_id": self.request.id,
        "status": "COMPLETED",
        "progress": 100
    }
    redis_client.publish("task_status", json.dumps(status_data))
    
    return result
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

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set Python path to include the root directory
ENV PYTHONPATH=/app

# Command to run the application - will be overridden by docker-compose
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Description of Code Snippet:**
- Defines a **Docker image** for the application using the slim version of Python 3.11.
- Installs dependencies from `requirements.txt` and copies the application code into the container.
- Runs the FastAPI application using Uvicorn.

---

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
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery-worker:
    build: .
    # Enable events for better Flower monitoring
    command: celery -A app.celery_worker worker --loglevel=info --events
    volumes:
      - .:/app
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - C_FORCE_ROOT=true  # To handle the superuser warning
    deploy:
      replicas: 2  # Default number of replicas
      resources:
        limits:
          cpus: '0.50'
          memory: 256M

  flower:
    build: .
    command: celery --broker=redis://redis:6379/0 -A app.celery_worker flower --port=5555
    ports:
      - "5555:5555"
    volumes:
      - .:/app
    depends_on:
      - redis
      - celery-worker
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379

volumes:
  redis_data:
```

**Description of Code Snippet:**
- Configures **Docker Compose** to orchestrate the `web`, `redis`, and `worker` services.
- The `web` service runs the FastAPI app.
- The `worker` service runs Celery workers for background task processing.
- The `redis` service acts as the message broker.

---

### 3. Create `requirements.txt`

```text name=requirements.txt
fastapi>=0.95.0
uvicorn>=0.21.1
jinja2>=3.1.2
celery>=5.2.7
redis>=4.5.4
websockets>=11.0.1
flower>=2.0.0  # Add Flower for monitoring
```

**Description of Code Snippet:**
- Lists the Python dependencies required for the application, including FastAPI, Celery, Redis, and Jinja2 for templating.

---
### Start the Application
Run the application using:
```bash
docker-compose up --build
```
**Description:**
- Builds the Docker images and starts the services defined in `docker-compose.yml`.
---


## Scaling Celery Workers

Scale Celery workers using Docker Compose:

```bash
docker-compose up --scale worker=3
```

**Description:**
- This command launches 3 instances of the `worker` service to handle tasks concurrently.

---



### Access the Web Interface
Open your browser and go to:
```
http://localhost:8000
```
![image](https://github.com/user-attachments/assets/e02bb32d-0887-4f07-ba36-fa1b454ec224)
![image](https://github.com/user-attachments/assets/a69a1aa3-d501-472a-8929-e28a50216136)


### Access the FLOWER Interface
```
http://localhost:5555
```
![image](https://github.com/user-attachments/assets/bf745dc6-c89c-4847-9d15-ebb12bac918a)
![image](https://github.com/user-attachments/assets/ce62a54c-c3ea-44b5-a0bd-4340ee7b24ca)

---

### Test WebSocket Integration
1. Open the developer console in your browser.
2. Go to the "Network" tab and filter for "WS" (WebSocket).
3. Start a task and observe WebSocket messages in real time.

**Description:**
- Verify that the WebSocket connection is established and receiving real-time updates for task progress.

