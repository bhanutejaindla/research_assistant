import os
import zipfile
import logging
from io import BytesIO
from datetime import datetime, timedelta
from typing import List

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import func
from github import Github, GithubException
from dotenv import load_dotenv

from models.model import User, Project

# -----------------------------
# Setup
# -----------------------------
load_dotenv()
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

CODE_EXTENSIONS = [
    ".py", ".js", ".java", ".cpp", ".c", ".cs", ".rb", ".go", ".rs",
    ".php", ".swift", ".kt", ".ts", ".scala"
]

# -----------------------------
# User Utilities
# -----------------------------
def get_user_by_email(db: Session, email: str):
    return (
        db.query(User)
        .filter(func.lower(User.email) == email.lower())
        .first()
    )


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


# -----------------------------
# Token Utilities
# -----------------------------
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# -----------------------------
# File & Repo Utilities
# -----------------------------
def has_code_files(file_list: List[str]) -> bool:
    return any(
        f.lower().endswith(tuple(CODE_EXTENSIONS)) and not f.startswith('.')
        for f in file_list
    )


async def check_zip_file(file):
    """Validate a ZIP file: ensure it's not empty and has code files."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max allowed is 10MB.")
    await file.seek(0)

    try:
        with zipfile.ZipFile(BytesIO(content)) as zf:
            file_list = zf.namelist()
            if not file_list:
                raise HTTPException(status_code=400, detail="ZIP file is empty.")
            if not has_code_files(file_list):
                raise HTTPException(status_code=400, detail="No recognizable code files found in ZIP.")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Corrupted or invalid ZIP file.")


def check_github_repo(github_url: str) -> bool:
    """Validate GitHub repo — ensures it's public and contains code files."""
    try:
        repo_path = github_url.replace("https://github.com/", "").strip("/").rstrip(".git")
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(repo_path)

        if repo.private:
            raise HTTPException(status_code=400, detail="Repository is private or inaccessible.")

        all_files = []
        stack = repo.get_contents("")
        while stack:
            file_content = stack.pop()
            if file_content.type == "dir":
                stack.extend(repo.get_contents(file_content.path))
            else:
                all_files.append(file_content.path)

        if not has_code_files(all_files):
            raise HTTPException(status_code=400, detail="No recognizable code files found in the repository.")

        return True

    except GithubException as e:
        raise HTTPException(status_code=400, detail=f"GitHub error: {str(e.data.get('message', e))}")
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed GitHub URL or repository inaccessible.")
