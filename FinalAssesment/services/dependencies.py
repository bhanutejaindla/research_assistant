import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_dependencies(repo_path: str):
    """
    Parses dependencies for Python, Node.js, Go, and Java (Maven) projects.
    
    Args:
        repo_path (str): Path to the root of the repository.
    
    Returns:
        dict: A dictionary of detected dependencies.
    """
    root = Path(repo_path)
    deps = {"python": [], "node": [], "other": []}

    # ----------------------------------------------------------------------
    # Python dependencies
    # ----------------------------------------------------------------------
    req = root / "requirements.txt"
    if req.exists():
        with open(req, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    deps["python"].append(line)

    # pyproject.toml (Poetry or modern Python builds)
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            import toml
            data = toml.load(pyproject)
            tool = data.get("tool", {})
            poetry = tool.get("poetry", {})
            if poetry:
                for name, v in poetry.get("dependencies", {}).items():
                    deps["python"].append(f"{name}=={v}" if isinstance(v, str) else name)
        except Exception as e:
            logger.info(f"⚠️ Failed to parse pyproject.toml: {e}")

    # ----------------------------------------------------------------------
    # Node.js dependencies
    # ----------------------------------------------------------------------
    pkg = root / "package.json"
    if pkg.exists():
        try:
            with open(pkg, "r", encoding="utf-8") as f:
                j = json.load(f)
                for group in ("dependencies", "devDependencies", "peerDependencies"):
                    if group in j:
                        for name, ver in j[group].items():
                            deps["node"].append(f"{name}@{ver}")
        except Exception as e:
            logger.info(f"⚠️ Failed to parse package.json: {e}")

    # ----------------------------------------------------------------------
    # Go dependencies
    # ----------------------------------------------------------------------
    go_mod = root / "go.mod"
    if go_mod.exists():
        try:
            with open(go_mod, "r", encoding="utf-8") as f:
                lines = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("//")
                ]
                # Only store first few for brevity
                deps["other"].extend(lines[:50])
        except Exception as e:
            logger.info(f"⚠️ Failed to parse go.mod: {e}")

    # ----------------------------------------------------------------------
    # Java (Maven) dependencies
    # ----------------------------------------------------------------------
    pom = root / "pom.xml"
    if pom.exists():
        deps["other"].append("pom.xml")

    return deps
