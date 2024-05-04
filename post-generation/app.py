import os

from flask_cors import CORS
from flask import Flask, request
from flask_restful import Resource, Api
from databases.postgresql import PostgresDB
from models.embedding_models import EmbeddingModel
from models.embedding_models import LargeLanguageModel
from services.tweet_vector_query_service import tweet_vector_query
from constant.prompt import RAGPrompt, NormalPrompt

app = Flask(__name__)
cors = CORS(app, resources={r"*": {"origins": "*"}})
api = Api(app)
model = EmbeddingModel()._embed_model
vector_store=PostgresDB().vetor_store
llm = LargeLanguageModel()._embed_model
#normprompt = NormalPrompt().prompt

class PostGenerationWithRAG(Resource):
    def get(self):
        return """ Welcome to post generation task, I am is LLM and I'll help to generate your marketing post """ 
    def post(self):
        #try:
            user_input = request.get_json()
        
            keywords = user_input['keyWords']
            simi_tweets = tweet_vector_query(
                EmbedModel=model,
                vector_store=vector_store,
                input=keywords,top_simi=10)
            if ('rag' in user_input):
                return  simi_tweets  
            else:
                
                ragprompt = RAGPrompt(
                    user_order=user_input,
                    references=simi_tweets
                ).prompt
                output_post = llm(ragprompt)  
                return output_post
        #except Exception as error:
         #   return {'error': error}
        

api.add_resource(PostGenerationWithRAG,'/')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1201))
    print(port)
    app.run(host='0.0.0.0', port=port, debug=True)