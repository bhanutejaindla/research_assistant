# services/preprocessing.py
import os
import json
from services.event_manager import EventManager

async def preprocess_repository(repo_path: str, event_manager: EventManager):
    await event_manager.send(0, "Preprocessing repository...")

    metadata = {
        "entry_points": [],
        "config_files": [],
        "dependencies": [],
        "language": None,
        "file_count": 0
    }

    for root, _, files in os.walk(repo_path):
        for file in files:
            path = os.path.join(root, file)
            metadata["file_count"] += 1

            # Detect entry points
            if file in ["main.py", "index.js", "app.py"]:
                metadata["entry_points"].append(path)

            # Detect configs
            if file in ["package.json", "requirements.txt", "pyproject.toml"]:
                metadata["config_files"].append(path)

            # Dependency detection
            if file == "requirements.txt":
                with open(path) as f:
                    metadata["dependencies"] = f.read().splitlines()

    await event_manager.send(0, f"Detected {metadata['file_count']} files")
    await event_manager.send(0, "Preprocessing complete")

    return metadata