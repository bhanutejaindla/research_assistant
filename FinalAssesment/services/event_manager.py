# # services/event_manager.py
# import asyncio
# from collections import defaultdict

# class EventManager:
#     def __init__(self):
#         self.listeners = defaultdict(list)

#     async def send(self, project_id: int, message: str):
#         for queue in self.listeners[project_id]:
#             await queue.put(message)

#     async def listen(self, project_id: int):
#         queue = asyncio.Queue()
#         self.listeners[project_id].append(queue)
#         try:
#             while True:
#                 message = await queue.get()
#                 yield message
#         finally:
#             self.listeners[project_id].remove(queue)

import asyncio
from typing import Dict, List, AsyncGenerator

class EventManager:
    def __init__(self):
        # project_id -> list of asyncio queues
        self.connections: Dict[int, List[asyncio.Queue]] = {}

    async def send(self, project_id: int, message: str):
        """Send message to all connected listeners for a given project."""
        if project_id not in self.connections:
            return

        for queue in self.connections[project_id]:
            await queue.put(message)

    async def listen(self, project_id: int) -> AsyncGenerator[str, None]:
        """Generator to stream messages for a specific project."""
        queue = asyncio.Queue()

        if project_id not in self.connections:
            self.connections[project_id] = []
        self.connections[project_id].append(queue)

        try:
            while True:
                # Wait for next message
                message = await queue.get()
                yield message
        finally:
            # Remove queue when client disconnects
            self.connections[project_id].remove(queue)
            if not self.connections[project_id]:
                del self.connections[project_id]
