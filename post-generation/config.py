import os

from dotenv import load_dotenv

load_dotenv()

class PostgresRAGDBConfig:
    CONNECTION_URL = os.environ.get("POSTGRES_RAG_CONNECTION_URL")
    EMBEDDING_TABLE = os.environ.get("POSTGRES_RAG_TABLE")
class MongoDBConfig:
    CONNECTION_URL = os.getenv("MONGODB_CONNECTION_URL")
    DATABASE = os.getenv("MONGODB_DATABASE")

class EmbeddingModels:
    MODEL_NAME = os.getenv("EMBEDDING_MODEL")