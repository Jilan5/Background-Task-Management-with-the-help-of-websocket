# Tutorial: Building a Scalable Background Task Processing System with WebSockets, Celery, Redis, and FastAPI

## Objectives
By the end of this tutorial, you will be able to:
1. Understand the architecture and components of a scalable background task processing system.
2. Implement WebSocket integration in FastAPI for real-time updates.
3. Use Celery and Redis for task management and message brokering.
4. Auto-scale Celery workers to handle dynamic workloads.
5. Deploy the application to AWS with multi-instance scaling.

---

## Introduction

Modern web applications often require background task processing for resource-intensive or time-consuming operations. Examples include video encoding, file processing, or periodic data updates. This tutorial will guide you step-by-step to build a scalable system using **FastAPI**, **WebSockets**, **Celery**, **Redis**, and **Docker**.

We'll also explore how WebSockets enable real-time task updates for clients and how Celery workers can be scaled for high throughput.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Setting Up the Environment](#setting-up-the-environment)
3. [Implementing WebSocket Integration](#implementing-websocket-integration)
4. [Integrating Celery for Background Tasks](#integrating-celery-for-background-tasks)
5. [Auto-Scaling Celery Workers](#auto-scaling-celery-workers)
6. [Deploying to AWS EC2 with Scaling](#deploying-to-aws-ec2-with-scaling)
7. [Testing WebSocket and Scaling](#testing-websocket-and-scaling)

---

## System Architecture

Before diving into implementation, let’s understand the architecture:

1. **FastAPI**: Handles client requests and exposes WebSocket endpoints for real-time updates.
2. **Redis**: Acts as the message broker for Celery and also as a pub/sub system for WebSocket updates.
3. **Celery**: Executes background tasks, offloading work from the main application thread.
4. **WebSockets**: Provides real-time communication between the server and clients.
5. **Docker**: Simplifies environment management and deployment.
6. **AWS**: Hosts the application and enables scaling with multiple EC2 instances.

![Architecture Diagram Placeholder](#)  
(Insert architecture diagram here)

---

## Setting Up the Environment

### 1. Prerequisites
- Python 3.11 or higher
- Docker and Docker Compose
- Basic understanding of FastAPI, Celery, and WebSockets
- AWS account for deployment

### 2. Clone the Repository
Clone the repository to your local machine:
```bash
git clone https://github.com/YourUsername/YourRepository.git
cd YourRepository
```

### 3. Install Dependencies
Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Start Docker Services
Build and start the services using Docker Compose:
```bash
docker-compose up --build
```

---

## Implementing WebSocket Integration

### What Are WebSockets?

WebSockets provide a full-duplex communication channel over a single TCP connection. Unlike HTTP, which is request-response-based, WebSockets allow the server to push updates to the client in real-time.

### How WebSockets Are Used in This Application

In this application:
- A **WebSocket endpoint** is exposed at `/ws`.
- Clients connect to this endpoint and listen for updates.
- Redis publishes task progress updates, which are then broadcast via WebSockets.

### Server-Side Implementation

1. **Connection Manager**: Manages active WebSocket connections.
2. **WebSocket Endpoint**: Handles client connections and disconnections.
3. **Redis Listener**: Listens for task updates on the "task_status" Redis channel and broadcasts them to connected clients.

```python name=app/main.py
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket data: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

**Client-Side Implementation**  
```javascript
const ws = new WebSocket(`ws://${window.location.host}/ws`);
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Task Update:', data);
};
```

---

## Integrating Celery for Background Tasks

### What Is Celery?

Celery is an asynchronous task queue/job queue based on distributed message passing. It enables you to offload tasks to worker processes, freeing your main application thread for other operations.

### How Celery Works with Redis

1. **Redis** acts as a broker to pass messages between FastAPI and Celery workers.
2. Workers pull tasks from the Redis queue and execute them asynchronously.

### Task Implementation

Define a task in `celery_worker.py`:
```python name=app/celery_worker.py
@celery.task(name="create_task", bind=True)
def create_task(self, task_length):
    for i in range(task_length):
        self.update_state(state="PROGRESS", meta={"progress": i})
        time.sleep(1)
    return {"status": "Task completed"}
```

---

## Auto-Scaling Celery Workers

### Why Auto-Scaling?

Auto-scaling adjusts the number of Celery workers based on workload, ensuring efficient resource usage and high performance during peak loads.

### Scaling with Docker Compose

Scale workers using the `--scale` flag:
```bash
docker-compose up --scale celery-worker=5
```

### Scaling in AWS

Use AWS Auto Scaling Groups to dynamically add or remove EC2 instances based on:
- CPU usage
- Redis queue length

(Insert workflow diagram for scaling)

---

## Deploying to AWS EC2 with Scaling

### 1. Set Up Infrastructure

1. **Create an ElastiCache Redis Cluster**: Use AWS ElastiCache to replace the local Redis container.
2. **Launch EC2 Instances**: Deploy separate instances for web servers and workers.

### 2. Configure Security Groups

- Allow Redis traffic only from web and worker instances.
- Open ports 8000 (HTTP) and 5555 (Flower) for external access.

### 3. Deploy Docker Containers

Run the following on each EC2 instance:
```bash
docker-compose up --build
```

---

## Testing WebSocket and Scaling

### WebSocket Testing

```bash
npm install -g wscat
wscat -c ws://<your-server-ip>:8000/ws
```

### Scaling Test

1. Start a large number of tasks:
```bash
for i in {1..100}; do curl -X POST http://<your-server-ip>:8000/tasks; done
```

2. Monitor worker activity on Flower:
```bash
http://<your-server-ip>:5555
```

---

## Placeholder for Diagrams

- **Architecture Diagram**
- **Workflow Diagram**
- **Sequence Diagram**

---

## Conclusion

In this tutorial, you learned how to build a scalable background task processing system with WebSockets, Celery, Redis, and FastAPI. You also explored auto-scaling strategies and deployed the application to AWS EC2.

Feel free to extend this project by:
- Adding more task types and queues.
- Enhancing WebSocket authentication.
- Deploying with Kubernetes for better orchestration.
