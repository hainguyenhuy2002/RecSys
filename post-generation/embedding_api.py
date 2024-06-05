from flasgger import Swagger
from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from models.embedding_models import EmbeddingModel
from services.tweet_vector_query_service import tweet_vector_query
from utils.logger_utils import get_logger
import time
import os

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)

logger = get_logger("PostGenerationService")
model = EmbeddingModel()._embed_model

@app.route('/get_embedding', methods=['POST'])
def get_embedding():
    data = request.get_json()
    input_keyword = data.get('input_keyword', '')

    if not input_keyword:
        return jsonify({'error': 'Input keyword is required'}), 400

    t1 = time.time()
    query_embedding = model.get_query_embedding(input_keyword)
    t2 = time.time()

    logger.info(f"Time for creating query_embedding: {t2 - t1} seconds")

    return query_embedding

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1201))
    print(port)
    app.run(host='0.0.0.0', port=port, debug=True)