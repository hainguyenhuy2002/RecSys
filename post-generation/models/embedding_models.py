import os
from langchain_community.llms import Replicate
from utils.logger_utils import get_logger
from config import EmbeddingModelConfig, LLMModelConfig
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from flasgger import Swagger
from llama_index.llms.together import TogetherLLM
from openai import OpenAI

os.environ["TOGETHER_API_KEY"] = LLMModelConfig.MODEL_API


class EmbeddingModel:
    def __init__(self, model_name: str = None):
        if model_name == None:
            self._embed_model = HuggingFaceEmbedding(model_name=EmbeddingModelConfig.MODEL_NAME)
        else:
            self._embed_model = HuggingFaceEmbedding(model_name=model_name)

class LargeLanguageModel:
    def __init__(self, model_name: str = None, model_kwargs: dict = None):
        if (model_name == None) & (model_kwargs == None):
            self._embed_model = TogetherLLM(
                model=LLMModelConfig.MODEL_NAME,
                model_kwargs=LLMModelConfig.MODEL_KWARGS,
                api_key=LLMModelConfig.MODEL_API
            )
        elif (model_name != None) & (model_kwargs != None):
            self._embed_model = TogetherLLM(
                model=model_name,
                model_kwargs=model_kwargs,
                api_key=LLMModelConfig.MODEL_API
            )
        else:
            get_logger("Invalid initial input parameter")

