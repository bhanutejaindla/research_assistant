# agents/web_retriever/tools/semantic_search_tool.py
from fastmcp import FastMCP
from agents.web_retriever.config import POSTGRES_URI, EMBED_MODEL, VECTOR_DIM
from sqlalchemy import create_engine, Column, Integer, Text, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pgvector.sqlalchemy import Vector
from typing import Optional, Literal, List
import numpy as np

mcp = FastMCP("semantic-search-tool")

Base = declarative_base()
engine = create_engine(POSTGRES_URI)
Session = sessionmaker(bind=engine)

_model = None
def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBED_MODEL)
    return _model

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True)
    text = Column(Text)
    embedding = Column(Vector(VECTOR_DIM))

Base.metadata.create_all(engine)

def store(url: str, text: str) -> dict:
    session = Session()
    try:
        model = _load_model()
        emb = model.encode([text], normalize_embeddings=True)[0].tolist()

        # Upsert
        doc = session.query(Document).filter_by(url=url).first()
        if doc:
            doc.text = text
            doc.embedding = emb
        else:
            doc = Document(url=url, text=text, embedding=emb)
            session.add(doc)
        session.commit()
        return {"status": "stored", "url": url}
    except Exception as e:
        session.rollback()
        return {"error": f"Failed to store document: {str(e)}"}
    finally:
        session.close()

def search(query: str, top_k: int = 5) -> List[dict]:
    model = _load_model()
    q_emb = model.encode([query], normalize_embeddings=True)[0].tolist()
    session = Session()
    
    try:
        # Convert embedding list to proper format for PostgreSQL
        emb_str = "[" + ",".join(map(str, q_emb)) + "]"
        
        # Use parameterized query with text()
        sql_query = text("""
            SELECT url, text, embedding <#> :embedding::vector AS distance
            FROM documents
            ORDER BY distance ASC
            LIMIT :limit
        """)
        
        results = session.execute(
            sql_query,
            {"embedding": emb_str, "limit": top_k}
        ).fetchall()
        
        return [
            {"url": r[0], "snippet": r[1][:500], "distance": float(r[2])} 
            for r in results
        ]
    except Exception as e:
        print(f"Search error: {str(e)}")
        return []
    finally:
        session.close()

# Implementation function (no decorator)
def _semantic_search_impl(
    action: Literal["store", "search"],
    url: Optional[str] = None,
    text: Optional[str] = None,
    query: Optional[str] = None,
    top_k: int = 5
) -> dict:
    try:
        if action == "store" and url and text:
            return store(url, text)
        elif action == "search" and query:
            results = search(query, top_k)
            return {"results": results}
        
        return {"error": "Invalid parameters. Store requires 'url' and 'text'. Search requires 'query'."}
    except Exception as e:
        return {"error": f"Operation failed: {str(e)}"}

# Register with MCP
@mcp.tool()
def semantic_search(
    action: Literal["store", "search"],
    url: Optional[str] = None,
    text: Optional[str] = None,
    query: Optional[str] = None,
    top_k: int = 5
) -> dict:
    """
    Embeds, stores, and searches web documents using PostgreSQL + pgvector.
    
    Args:
        action: Either "store" to index a document or "search" to query semantically
        url: Document URL (required for store action)
        text: Document text content (required for store action)
        query: Search query (required for search action)
        top_k: Number of top results to return for search (default: 5)
    
    Returns:
        Dictionary with status/results or error message
    """
    return _semantic_search_impl(action=action, url=url, text=text, query=query, top_k=top_k)

# Backwards compatibility
def run(action: str, url: str = None, text: str = None, query: str = None, top_k: int = 5):
    return _semantic_search_impl(action=action, url=url, text=text, query=query, top_k=top_k)

# Export
__all__ = ['semantic_search', 'store', 'search', 'run', 'mcp']

if __name__ == "__main__":
    mcp.run()