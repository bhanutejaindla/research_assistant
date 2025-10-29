import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def clone_repo(github_url: str, target_dir: str) -> None:
    """
    Clone a GitHub repository into the target directory.

    Args:
        github_url (str): The GitHub repository URL.
        target_dir (str): Local directory to clone into.

    Raises:
        subprocess.CalledProcessError: If the git command fails.
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Cloning repo from {github_url} to {target_dir}")
    print(f"Cloning repo from {github_url} to {target_dir}")

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", github_url, target_dir],
            check=True,
        )
        logger.info("Repository cloned successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git clone failed: {e}")
        raise RuntimeError(f"Git clone failed: {e}")
