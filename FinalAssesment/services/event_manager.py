import asyncio
import weakref
from typing import Dict

class EventManager:
    """
    Manages per-project async event queues for Server-Sent Events (SSE).

    Features:
      ✅ Creates a queue automatically when a listener or sender starts.
      ✅ Sends periodic keepalive events (to keep connections open).
      ✅ Cleans up disconnected clients to avoid memory leaks.
    """

    def __init__(self):
        # Weak reference dictionary to auto-clean unused queues
        self.listeners: Dict[int, asyncio.Queue] = weakref.WeakValueDictionary()
        self.keepalive_interval = 10  # seconds

    async def ensure_queue(self, project_id: int) -> asyncio.Queue:
        """Ensure a queue exists for the given project_id."""
        if project_id not in self.listeners:
            self.listeners[project_id] = asyncio.Queue()
        return self.listeners[project_id]

    async def send(self, project_id: int, message: str):
        """Send an event message to all listeners of a given project."""
        queue = await self.ensure_queue(project_id)
        await queue.put(message)

    async def listen(self, project_id: int):
        """
        Listen for events from a specific project queue.
        This is an async generator that yields messages for StreamingResponse.
        """
        queue = await self.ensure_queue(project_id)

        try:
            while True:
                try:
                    # Wait for next event or send keepalive
                    event = await asyncio.wait_for(queue.get(), timeout=self.keepalive_interval)
                    yield event
                except asyncio.TimeoutError:
                    # Keep connection alive
                    yield ":keepalive"
        except asyncio.CancelledError:
            # Client disconnected — clean up
            if project_id in self.listeners:
                del self.listeners[project_id]
            raise
        except Exception as e:
            # Handle unexpected errors gracefully
            yield f"Error: {str(e)}"

    async def close(self, project_id: int):
        """Manually close the listener for a given project."""
        if project_id in self.listeners:
            del self.listeners[project_id]
