import os
import logging
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    Integer,
    String,
    MetaData,
    JSON,
    Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------
# Database Setup
# ------------------------------------------------------------------
DATABASE_URL = os.getenv("CONNECTION_URL")
if not DATABASE_URL:
    raise ValueError("❌ Missing CONNECTION_URL in environment variables.")

engine = create_engine(DATABASE_URL)
metadata = MetaData()

# ------------------------------------------------------------------
# Table Definition
# ------------------------------------------------------------------
project_files_table = Table(
    "project_files",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, nullable=False, index=True),
    Column("path", String, nullable=False),
    Column("file_type", String, nullable=False),
    Column("metadata", JSONB),
)

# Create the table if not already present
metadata.create_all(engine)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Store Metadata Function
# ------------------------------------------------------------------
def store_metadata(project_id: int, metadata_dict: dict):
    """
    Stores parsed repository metadata into PostgreSQL.
    Each file/directory entry is saved in 'project_files' table.
    """
    root_meta = metadata_dict.get("structure", [])
    if not isinstance(root_meta, list):
        logger.error("Expected 'structure' to be a list in metadata_dict.")
        return

    conn = engine.connect()
    trans = conn.begin()

    try:
        for node in root_meta:
            # Defensive programming: skip invalid nodes
            if not isinstance(node, dict):
                logger.warning(f"Skipping non-dict node: {node}")
                continue

            entry = {
                "project_id": project_id,
                "path": node.get("path", ""),
                "file_type": "dir" if node.get("is_dir") else node.get("ext", "file"),
                "metadata": {
                    "size": node.get("size"),
                    "is_dir": node.get("is_dir"),
                },
            }

            conn.execute(project_files_table.insert().values(**entry))

        trans.commit()
        logger.info(f"✅ Metadata for project {project_id} stored successfully.")

    except SQLAlchemyError as e:
        trans.rollback()
        logger.exception(f"❌ Database error while storing metadata: {e}")
        raise

    finally:
        conn.close()
