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

class Test(Resource):
    def get(self):
        return 'Welcome to Generative model :>>!'

    def post(self):
        try:
            value = request.get_text()
            if(value):
                return {'Post Values': value}, 201

            return {"error":"Invalid format."}

        except Exception as error:
            return {'error': error}

class PostGenerationWithRAG(Resource):
    def get(self):
        return {"error":"Invalid Method."}
    def post(self):
        #try:
            user_input = request.get_json()
            keywords = user_input['keyWords']
            simi_tweets = tweet_vector_query(
                EmbedModel=model,
                vector_store=vector_store,
                input=keywords,top_simi=10)

            ragprompt = RAGPrompt(
                user_order=user_input,
                references=simi_tweets
            ).prompt
            output_post = llm(ragprompt)
            return output_post

        #except Exception as error:
         #   return {'error': error}
        
api.add_resource(Test,'/')
api.add_resource(PostGenerationWithRAG,'/PostGenerationWithRAG')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)