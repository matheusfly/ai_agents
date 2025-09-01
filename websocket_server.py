import os
import json
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.utils.websocket import websocket_manager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("websocket_server")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start WebSocket manager on startup"""
    await websocket_manager.start()
    logger.info("WebSocket manager started on startup")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop WebSocket manager on shutdown"""
    await websocket_manager.stop()
    logger.info("WebSocket manager stopped on shutdown")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # Extract client metadata from query parameters
    client_id = websocket.query_params.get("client_id", f"client_{id(websocket)}")
    metadata = {
        "user_agent": websocket.headers.get("user-agent", "unknown"),
        "ip": websocket.client.host
    }

    # Add to manager
    websocket_manager.add_client(client_id, websocket, metadata)
    logger.info(f"Client connected: {client_id}")

    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
    except:
        logger.info(f"Client disconnected: {client_id}")
    finally:
        websocket_manager.remove_client(client_id)

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "clients": len(websocket_manager.clients),
        "queue_size": websocket_manager.message_queue.qsize() if websocket_manager.message_queue else 0
    }

if __name__ == "__main__":
    port = int(os.getenv("WEBSOCKET_PORT", 3001))
    logger.info(f"Starting WebSocket server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
