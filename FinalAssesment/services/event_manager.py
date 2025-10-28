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

# 


# services/event_manager.py
import asyncio
from typing import Dict, Set
from collections import defaultdict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        try:
            async with self._lock:
                logger.info(f"Sending message to project {project_id}: {message[:100]}...")
                
                # Store in history for late joiners
                history = self._message_history[project_id]
                history.append(message)
                if len(history) > self._max_history:
                    history.pop(0)
                
                # Send to all active listeners
                if project_id in self.listeners:
                    dead_queues = set()
                    active_count = 0
                    
                    for queue in self.listeners[project_id]:
                        try:
                            # Use put_nowait to avoid blocking
                            queue.put_nowait(message)
                            active_count += 1
                        except asyncio.QueueFull:
                            # Queue is full, mark for removal
                            logger.warning(f"Queue full for project {project_id}, marking for removal")
                            dead_queues.add(queue)
                    
                    # Remove dead queues
                    if dead_queues:
                        self.listeners[project_id] -= dead_queues
                        logger.info(f"Removed {len(dead_queues)} dead queues for project {project_id}")
                    
                    logger.info(f"Message sent to {active_count} active listeners for project {project_id}")
                else:
                    logger.info(f"No active listeners for project {project_id}, message stored in history")
        
        except Exception as e:
            logger.error(f"Error sending message to project {project_id}: {str(e)}")
    
    async def listen(self, project_id: int):
        """Listen to events for a project"""
        queue = asyncio.Queue(maxsize=100)
        
        async with self._lock:
            # Register this listener
            self.listeners[project_id].add(queue)
            logger.info(f"New listener registered for project {project_id}. Total listeners: {len(self.listeners[project_id])}")
            
            # Send message history to catch up
            history = self._message_history.get(project_id, [])
        
        try:
            # First, yield all historical messages
            logger.info(f"Sending {len(history)} historical messages to new listener for project {project_id}")
            for message in history:
                yield message
            
            # Then yield new messages as they arrive
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                    
                    # Check if this is a terminal message
                    if any(term in event.lower() for term in ["complete", "failed", "error"]):
                        logger.info(f"Terminal message detected for project {project_id}: {event[:100]}")
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive to detect disconnections
                    yield ":keepalive"
        
        except asyncio.CancelledError:
            logger.info(f"Listener cancelled for project {project_id}")
            raise
        
        except Exception as e:
            logger.error(f"Error in listener for project {project_id}: {str(e)}")
            raise
        
        finally:
            # Cleanup when listener disconnects
            async with self._lock:
                self.listeners[project_id].discard(queue)
                logger.info(f"Listener disconnected from project {project_id}. Remaining listeners: {len(self.listeners[project_id])}")
                
                if not self.listeners[project_id]:
                    # Last listener disconnected, clean up
                    logger.info(f"Last listener disconnected from project {project_id}, cleaning up")
                    del self.listeners[project_id]
                    # Optionally clear history (uncomment if you want to clear history when no listeners)
                    # if project_id in self._message_history:
                    #     del self._message_history[project_id]
    
    def get_listener_count(self, project_id: int) -> int:
        """Get the number of active listeners for a project"""
        return len(self.listeners.get(project_id, set()))
    
    def get_message_history(self, project_id: int) -> list:
        """Get message history for a project"""
        return self._message_history.get(project_id, []).copy()
    
    async def clear_history(self, project_id: int):
        """Clear message history for a project"""
        async with self._lock:
            if project_id in self._message_history:
                del self._message_history[project_id]
                logger.info(f"Cleared message history for project {project_id}")
    
    async def disconnect_all(self, project_id: int):
        """Disconnect all listeners for a project"""
        async with self._lock:
            if project_id in self.listeners:
                # Close all queues by putting None
                for queue in self.listeners[project_id]:
                    try:
                        queue.put_nowait(None)
                    except asyncio.QueueFull:
                        pass
                
                # Clear listeners
                del self.listeners[project_id]
                logger.info(f"Disconnected all listeners for project {project_id}")