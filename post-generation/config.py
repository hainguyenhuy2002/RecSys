import os

from dotenv import load_dotenv

load_dotenv()

class PostgresRAGDBConfig:
    CONNECTION_URL = os.environ.get("POSTGRES_RAG_CONNECTION_URL")
    EMBEDDING_TABLE = os.environ.get("POSTGRES_RAG_TABLE")
class MongoDBConfig:
    CONNECTION_URL = os.getenv("MONGODB_CONNECTION_URL")
    DATABASE = os.getenv("MONGODB_DATABASE")

class EmbeddingModelConfig:
    MODEL_NAME = os.getenv("EMBEDDING_MODEL")
class LLMModelConfig:
    MODEL_NAME = os.getenv("LARGE_LANGUAGE_MODEL")
    MODEL_API = os.getenv("REPLICATE_API")
    MODEL_KWARGS={
        "temperature": 0.75, 
        "max_length": 500, 
        "top_p": 1
        }
