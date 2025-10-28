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

# import asyncio
# from typing import Dict, List, AsyncGenerator

# class EventManager:
#     def __init__(self):
#         # project_id -> list of asyncio queues
#         self.connections: Dict[int, List[asyncio.Queue]] = {}

#     async def send(self, project_id: int, message: str):
#         """Send message to all connected listeners for a given project."""
#         if project_id not in self.connections:
#             return

#         for queue in self.connections[project_id]:
#             await queue.put(message)

#     async def listen(self, project_id: int) -> AsyncGenerator[str, None]:
#         """Generator to stream messages for a specific project."""
#         queue = asyncio.Queue()

#         if project_id not in self.connections:
#             self.connections[project_id] = []
#         self.connections[project_id].append(queue)

#         try:
#             while True:
#                 # Wait for next message
#                 message = await queue.get()
#                 yield message
#         finally:
#             # Remove queue when client disconnects
#             self.connections[project_id].remove(queue)
#             if not self.connections[project_id]:
#                 del self.connections[project_id]

import asyncio
from typing import Dict, Set
from collections import defaultdict

class EventManager:
    def __init__(self):
        # Use a set of queues per project to support multiple listeners
        self.listeners: Dict[int, Set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()
        # Store messages for late-joining clients
        self._message_history: Dict[int, list] = defaultdict(list)
        self._max_history = 50  # Keep last 50 messages
    
    async def send(self, project_id: int, message: str):
        """Send message to all active listeners"""
        async with self._lock:
            # Store in history for late joiners
            history = self._message_history[project_id]
            history.append(message)
            if len(history) > self._max_history:
                history.pop(0)
            
            # Send to all active listeners
            if project_id in self.listeners:
                dead_queues = set()
                for queue in self.listeners[project_id]:
                    try:
                        # Use put_nowait to avoid blocking
                        queue.put_nowait(message)
                    except asyncio.QueueFull:
                        # Queue is full, mark for removal
                        dead_queues.add(queue)
                
                # Remove dead queues
                self.listeners[project_id] -= dead_queues
    
    async def listen(self, project_id: int):
        """Listen to events for a project"""
        queue = asyncio.Queue(maxsize=100)
        
        async with self._lock:
            # Register this listener
            self.listeners[project_id].add(queue)
            
            # Send message history to catch up
            history = self._message_history.get(project_id, [])
        
        try:
            # First, yield all historical messages
            for message in history:
                yield message
            
            # Then yield new messages as they arrive
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                    
                    # Check if this is a terminal message
                    if any(term in event.lower() for term in ["complete", "failed", "error"]):
                        break
                except asyncio.TimeoutError:
                    # Send keepalive to detect disconnections
                    yield ":keepalive"
        
        finally:
            # Cleanup when listener disconnects
            async with self._lock:
                self.listeners[project_id].discard(queue)
                if not self.listeners[project_id]:
                    # Last listener disconnected, clean up
                    del self.listeners[project_id]
                    # Optionally clear history
                    if project_id in self._message_history:
                        del self._message_history[project_id]