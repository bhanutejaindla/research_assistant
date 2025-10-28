# services/event_manager.py
import asyncio
from collections import defaultdict

class EventManager:
    def __init__(self):
        self.listeners = {}
        self.history = defaultdict(list)
        self.keepalive_interval = 10  # seconds

    async def ensure_queue(self, project_id: int):
        if project_id not in self.listeners:
            self.listeners[project_id] = asyncio.Queue()
        return self.listeners[project_id]

    async def send(self, project_id: int, message: str):
        """Send message to SSE queue and store in polling history"""
        self.history[project_id].append({"message": message})
        queue = await self.ensure_queue(project_id)
        await queue.put(message)

    async def listen(self, project_id: int):
        """Used by SSE endpoint"""
        queue = await self.ensure_queue(project_id)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=self.keepalive_interval)
                yield event
            except asyncio.TimeoutError:
                yield ":keepalive"

    async def get_events(self, project_id: int, last_index: int = 0):
        """Used by polling endpoint"""
        all_events = self.history.get(project_id, [])
        return all_events[last_index:], len(all_events)
