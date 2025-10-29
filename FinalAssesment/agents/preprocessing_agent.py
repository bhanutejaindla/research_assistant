import os
import zipfile
import tempfile
import requests
from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound
import ast


def extract_zip(zip_path, extract_to=None):
    """Extracts a zip file safely and returns a list of extracted file paths."""
    if extract_to is None:
        extract_to = tempfile.mkdtemp(prefix="unzipped_")

    files = []
    os.makedirs(extract_to, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        names = [os.path.normpath(m.filename) for m in zip_ref.infolist()]

        # Detect a redundant top-level folder (to flatten structure)
        prefixes = {name.split(os.sep)[0] for name in names if len(name.split(os.sep)) > 1}
        strip_prefix = list(prefixes)[0] if len(prefixes) == 1 else None

        for member in zip_ref.infolist():
            norm_filename = os.path.normpath(member.filename)

            # Skip dangerous paths
            if (
                norm_filename.startswith("..")
                or os.path.isabs(norm_filename)
                or norm_filename == ""
            ):
                continue

            # Remove redundant root folder
            if strip_prefix and norm_filename.startswith(strip_prefix + os.sep):
                norm_filename = norm_filename[len(strip_prefix) + 1:]

            member_path = os.path.join(extract_to, norm_filename)

            if member.is_dir():
                os.makedirs(member_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(member_path), exist_ok=True)
                try:
                    with zip_ref.open(member) as source, open(member_path, "wb") as target:
                        target.write(source.read())
                    files.append(member_path)
                except Exception as e:
                    print(f"Error extracting {member_path}: {e}")

    return files


def download_and_extract_github(github_url, extract_to=None):
    """Downloads a GitHub repo as zip and extracts it."""
    if extract_to is None:
        extract_to = tempfile.mkdtemp(prefix="github_repo_")

    parts = github_url.rstrip("/").split("/")
    repo = "/".join(parts[-2:])  # e.g. "username/repo"
    zip_url = f"https://github.com/{repo}/archive/refs/heads/main.zip"

    local_zip = os.path.join(extract_to, "repo.zip")

    try:
        r = requests.get(zip_url, timeout=15)
        r.raise_for_status()
        with open(local_zip, "wb") as f:
            f.write(r.content)
    except requests.exceptions.RequestException as e:
        print(f"Download exception: {e}")
        return []

    return extract_zip(local_zip, extract_to)


def detect_file_language(file_path):
    """Detects the programming language of a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        lexer = guess_lexer_for_filename(file_path, content)
        return lexer.name
    except (FileNotFoundError, ClassNotFound, UnicodeDecodeError):
        return "Unknown"


def extract_python_structure(file_path):
    """Extracts classes, functions, and imports from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)
        structure = {"classes": [], "functions": [], "imports": []}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                structure["classes"].append(node.name)
            elif isinstance(node, ast.FunctionDef):
                structure["functions"].append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    structure["imports"].append(alias.name)
        return structure
    except Exception as e:
        return {"error": str(e)}


def preprocessing_agent(state: dict) -> dict:
    """
    Handles preprocessing of uploaded zip or GitHub URL and updates the state.
    Extracts, detects languages, and summarizes code structure.
    """
    state.setdefault("agent_log", [])
    files = []

    try:
        if state.get("zip_path"):
            files = extract_zip(state["zip_path"])
            state["agent_log"].append(f"✅ Preprocessing Agent: Extracted {len(files)} files from ZIP.")
        elif state.get("github_url"):
            files = download_and_extract_github(state["github_url"])
            state["agent_log"].append(f"✅ Preprocessing Agent: Downloaded and extracted {len(files)} files from GitHub.")
        else:
            state["agent_log"].append("⚠️ Preprocessing Agent: No input ZIP or GitHub URL provided.")
            return state

        # Filter to only relevant text/code files
        code_extensions = (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".json", ".html", ".css", ".md", ".yml", ".yaml")
        code_files = [f for f in files if f.lower().endswith(code_extensions)]

        state["file_list"] = code_files
        state["unzipped_path"] = os.path.dirname(code_files[0]) if code_files else None

        detailed_info = []
        for file in code_files:
            file_info = {"file_path": file, "language": detect_file_language(file)}
            if file.endswith(".py"):
                file_info["structure"] = extract_python_structure(file)
            detailed_info.append(file_info)

        state["detailed_file_info"] = detailed_info
        state["agent_log"].append(f"🧠 Preprocessing Agent: Processed {len(detailed_info)} files with detailed structure.")
        state["agent_log"].append(f"📂 First few files: {[os.path.basename(f) for f in code_files[:5]]}")

    except Exception as e:
        state["agent_log"].append(f"❌ Preprocessing Agent: Error - {e}")

    return state
