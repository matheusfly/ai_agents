# utils/websocket.py
import asyncio
from typing import Dict, Any, Optional, List
import json
from collections import deque
import logging

logger = logging.getLogger("websocket_manager")

class WebSocketManager:
    """Enhanced WebSocket manager with backpressure handling and reliability"""

    def __init__(self, max_queue_size=1000, max_retries=3, retry_delay=0.1):
        self.clients: Dict[str, Any] = {}
        self.lock = asyncio.Lock()
        self.message_queue = asyncio.Queue(maxsize=max_queue_size)
        self.processing_task = None
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client_metadata = {}  # Track metadata for each client
        self.event_history: Dict[str, List[Dict[str, Any]]] = {} # Store event history

    async def start(self):
        """Start the WebSocket manager with error handling"""
        if self.processing_task is None or self.processing_task.done():
            self.processing_task = asyncio.create_task(self._process_queue())
            logger.info("WebSocket manager started")

    async def stop(self):
        """Safely stop the WebSocket manager"""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None
        logger.info("WebSocket manager stopped")

    def add_client(self, client_id: str, websocket: Any, metadata: Dict[str, Any] = None):
        """Add a new WebSocket client with metadata"""
        async def _add():
            async with self.lock:
                self.clients[client_id] = websocket
                self.client_metadata[client_id] = metadata or {}
            logger.info(f"✅ Added WebSocket client: {client_id} (Total: {len(self.clients)})")

        asyncio.create_task(_add())

    def remove_client(self, client_id: str):
        """Remove a WebSocket client and clean up resources"""
        async def _remove():
            async with self.lock:
                if client_id in self.clients:
                    del self.clients[client_id]
                if client_id in self.client_metadata:
                    del self.client_metadata[client_id]
            logger.info(f"❌ Removed WebSocket client: {client_id} (Total: {len(self.clients)})")

        asyncio.create_task(_remove())

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients and store it in history."""
        session_id = message.get("session_id")
        if session_id:
            if session_id not in self.event_history:
                self.event_history[session_id] = []
            self.event_history[session_id].append(message)

        try:
            await self.message_queue.put(message)
        except asyncio.QueueFull:
            logger.error("Message queue full, dropping message")

    def get_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all events for a given session_id."""
        return self.event_history.get(session_id, [])

    async def _process_queue(self):
        """Process messages from the queue with retry logic"""
        while True:
            try:
                message = await self.message_queue.get()
                await self._send_to_all(message)
                self.message_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message queue: {str(e)}")

    async def _send_to_all(self, message: Dict[str, Any]):
        """Send a message to all clients with retry logic"""
        async with self.lock:
            # Make a copy of clients to avoid modification during iteration
            clients = list(self.clients.items())

        for client_id, websocket in clients:
            await self._send_to_client(client_id, websocket, message)

    async def _send_to_client(self, client_id: str, websocket: Any, message: Dict[str, Any]):
        """Send a message to a specific client with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                if websocket.open:
                    await websocket.send(json.dumps(message))
                    return  # Success
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for client {client_id}: {str(e)}")
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"Failed to send to client {client_id} after {self.max_retries} attempts")
                    self.remove_client(client_id)

# Global instance
websocket_manager = WebSocketManager()
