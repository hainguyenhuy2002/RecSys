from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from config import EmbeddingModels

class EmbeddingModel:
    def __init__(self, model_name: str = None):
        if model_name ==None:
            self.embed_model = HuggingFaceEmbedding(model_name=EmbeddingModels.MODEL_NAME)
        else:
            self.embed_model = HuggingFaceEmbedding(model_name=model_name)