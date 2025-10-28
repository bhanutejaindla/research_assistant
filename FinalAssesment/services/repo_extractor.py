# services/repo_extractor.py
import os
import zipfile
import tempfile
import shutil
import asyncio
from services.event_manager import EventManager

async def extract_repo(project, event_manager: EventManager) -> str:
    """
    Extracts a ZIP file or clones a GitHub repo asynchronously.
    Returns path to extracted repo folder.
    """
    await event_manager.send(project.id, "📦 Starting repository extraction...")

    extract_path = tempfile.mkdtemp(prefix="repo_")

    try:
        # --- ZIP Extraction ---
        if project.source_type == "ZIP" and project.source_zip_path:
            zip_path = project.source_zip_path
            if not os.path.exists(zip_path):
                raise FileNotFoundError(f"ZIP file not found at {zip_path}")

            await event_manager.send(project.id, f"📁 Extracting ZIP: {zip_path}")
            await asyncio.to_thread(extract_zip_safe, zip_path, extract_path)
            await event_manager.send(project.id, f"✅ ZIP extracted to {extract_path}")
            return extract_path

        # --- GitHub Clone ---
        elif project.source_type == "GITHUB" and project.source_github_url:
            repo_url = project.source_github_url
            await event_manager.send(project.id, f"🔗 Cloning repository: {repo_url}")

            process = await asyncio.create_subprocess_shell(
                f"git clone --depth 1 {repo_url} {extract_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
            except asyncio.TimeoutError:
                process.kill()
                raise TimeoutError("Git clone operation timed out.")

            if process.returncode != 0:
                err = stderr.decode().strip()
                await event_manager.send(project.id, f"❌ Git clone failed: {err}")
                raise RuntimeError(f"Git clone failed: {err}")

            await event_manager.send(project.id, f"✅ Repo cloned to {extract_path}")
            return extract_path

        else:
            raise ValueError("Invalid project source type. Expected 'ZIP' or 'GITHUB'.")

    except Exception as e:
        await event_manager.send(project.id, f"❌ Extraction error: {e}")
        # Cleanup if something goes wrong
        shutil.rmtree(extract_path, ignore_errors=True)
        raise

def extract_zip_safe(zip_path: str, extract_path: str):
    """Thread-safe ZIP extraction to avoid blocking async event loop."""
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
