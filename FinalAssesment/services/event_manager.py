# services/event_manager.py
import asyncio
from collections import defaultdict

class EventManager:
    def __init__(self):
        self.listeners = defaultdict(list)

    async def send(self, project_id: int, message: str):
        for queue in self.listeners[project_id]:
            await queue.put(message)

    async def listen(self, project_id: int):
        queue = asyncio.Queue()
        self.listeners[project_id].append(queue)
        try:
            while True:
                message = await queue.get()
                yield message
        finally:
            self.listeners[project_id].remove(queue)
