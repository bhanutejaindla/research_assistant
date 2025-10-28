import asyncio

class EventManager:
    def __init__(self):
        # Each project_id will have its own asyncio.Queue
        self.listeners = {}

    async def send(self, project_id: int, message: str):
        """Send a message to listeners of a project"""
        if project_id not in self.listeners:
            self.listeners[project_id] = asyncio.Queue()
        await self.listeners[project_id].put(message)

    async def listen(self, project_id: int):
        """Async generator yielding messages for a given project"""
        if project_id not in self.listeners:
            self.listeners[project_id] = asyncio.Queue()
        queue = self.listeners[project_id]

        # Send periodic keepalive messages
        async def keepalive():
            while True:
                await asyncio.sleep(15)
                await queue.put(":keepalive")

        asyncio.create_task(keepalive())

        while True:
            event = await queue.get()
            yield event
