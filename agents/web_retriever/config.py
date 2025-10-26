# agents/web_retriever/config.py
POSTGRES_URI = "postgresql+psycopg2://username:password@localhost:5432/web_retriever_db"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_DIM = 384
FETCH_TIMEOUT = 15
USER_AGENT = "MCP-WebRetriever/1.0"
