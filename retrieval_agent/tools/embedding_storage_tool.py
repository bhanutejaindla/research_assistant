import os
from dotenv import load_dotenv
from openai import OpenAI
import psycopg2
from pgvector.psycopg2 import register_vector

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# Connect to PostgreSQL
conn = psycopg2.connect(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
register_vector(conn)
cur = conn.cursor()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def store_embedding(document_text: str):
    """Generate OpenAI embedding and store in PostgreSQL"""
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=document_text
    )
    embedding_vector = response.data[0].embedding

    cur.execute(
        "INSERT INTO documents (content, embedding) VALUES (%s, %s)",
        (document_text, embedding_vector)
    )
    conn.commit()
    return "Stored successfully"

def query_similar_documents(query_text: str, top_k: int = 5):
    """Generate query embedding and fetch top-k similar documents"""
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=query_text
    )
    query_embedding = response.data[0].embedding

    cur.execute("""
        SELECT content
        FROM documents
        ORDER BY embedding <-> %s
        LIMIT %s
    """, (query_embedding, top_k))

    results = cur.fetchall()
    return [r[0] for r in results]
