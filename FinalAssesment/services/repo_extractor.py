import os
import zipfile
import tempfile
import shutil
import asyncio
from services.event_manager import EventManager

async def extract_repo(project, event_manager: EventManager):
    """Extracts a ZIP file or clones a GitHub repo"""
    await event_manager.send(project.id, "Starting repository extraction...")

    if project.source_type == "ZIP" and project.source_zip_path:
        extract_path = tempfile.mkdtemp(prefix="repo_")
        await event_manager.send(project.id, f"Extracting ZIP: {project.source_zip_path}")
        with zipfile.ZipFile(project.source_zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        await event_manager.send(project.id, f"ZIP extracted to {extract_path}")
        return extract_path

    elif project.source_type == "GITHUB" and project.source_github_url:
        extract_path = tempfile.mkdtemp(prefix="repo_")
        await event_manager.send(project.id, f"Cloning repository: {project.source_github_url}")
        process = await asyncio.create_subprocess_shell(
            f"git clone {project.source_github_url} {extract_path}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            await event_manager.send(project.id, f"Git clone failed: {stderr.decode()}")
            raise Exception(f"Failed to clone repo: {stderr.decode()}")
        await event_manager.send(project.id, f"Repo cloned to {extract_path}")
        return extract_path

    else:
        raise ValueError("Invalid project source type")
