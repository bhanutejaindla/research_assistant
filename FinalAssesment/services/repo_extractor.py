# services/repo_extractor.py
import os
import tempfile
import shutil
import zipfile
import git
from services.event_manager import EventManager
from models.model import Project

async def extract_repo(project: Project, event_manager: EventManager):
    await event_manager.send(project.id, "Extracting repository...")

    tmp_dir = tempfile.mkdtemp()

    if project.source_type == "ZIP" and project.source_zip_path:
        with zipfile.ZipFile(project.source_zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
    elif project.source_type == "GITHUB" and project.source_github_url:
        git.Repo.clone_from(project.source_github_url, tmp_dir)
    else:
        raise ValueError("Invalid project source type")

    await event_manager.send(project.id, "Repository extraction complete")
    return tmp_dir
