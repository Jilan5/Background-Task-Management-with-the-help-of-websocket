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