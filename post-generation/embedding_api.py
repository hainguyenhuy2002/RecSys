from flasgger import Swagger
from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from models.embedding_models import EmbeddingModel
from services.tweet_vector_query_service import tweet_vector_query
from databases.postgresql import PostgresDB
from models.embedding_models import LargeLanguageModel
from constant.prompt import RAGPrompt
from llama_index.core.vector_stores import VectorStoreQuery
from utils.logger_utils import get_logger
import time
import os
import emoji
import re

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)

logger = get_logger("PostGenerationService")
model = EmbeddingModel()._embed_model
vector_store = PostgresDB().vector_store
vector_store_v2 = PostgresDB().vector_store_v2
db = PostgresDB()
llm = LargeLanguageModel()._embed_model


def clean_generated_content(content):
    max_hashtags = 5
    # Remove system notes or character count indicators enclosed in any brackets or common phrases
    patterns_to_remove = [
        r'<<.*?>>',   
        r'<.*?>',            
        r'\([^)]*\)',            
        r'\[[^\]]*\]',             
        r'I hope this.*?',
        r'.*?Note.*?|.*?note.\*?|.*?Sure.*?\n\n|.*?sure.*?\n\n',
        r'.*?Please let me know.*?\n\n', 
        r".*?Here's.*?\n\n",
        r".*?Here are.*?\n\n",
        r".*?Here is.*?\n\n", 
        r"Here is the final version of the post:\n\n", 
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Normalize whitespace, keeping double newlines
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n\n\n', '\n\n', content)
    content = content.strip()

    hashtags = re.findall(r'#\w+', content)
    if len(hashtags) > max_hashtags:
        content = re.sub(r'#\w+', '', content)
        content += ' ' + ' '.join(hashtags[:max_hashtags])
    
    # If the content has no "\n\n", please replace "\n" with "\n\n"
    if content.count('\n') == 1 and content.count('\n\n') == 0:
        content = content.replace('\n', '\n\n')
    
    # If the content has no any '\n', please add '\n\n' after the first sentence
    if content.count('\n') == 0 and content.count('\n\n') == 0:
        content = content.replace('. ', '.\n\n')
    
    return content


@app.route('/get_embedding', methods=['POST'])
def get_embedding():
    references = {}
    data = request.get_json()
    input_keyword = data.get('input_keyword', '')
    social_platform = data.get('social_platform', '')

    if not input_keyword:
        return jsonify({'error': 'Input keyword is required'}), 400

    t1 = time.time()

    if social_platform.lower() == 'twitter':
        tweet_simi = tweet_vector_query(model, vector_store, input_keyword, 10)
        for key, value in tweet_simi.items():
            if len(value) < 350:
                references[key] = value
            else:
                continue

    elif social_platform.lower() == 'telegram':
        references = tweet_vector_query(model, vector_store_v2, input_keyword, 10)

    t2 = time.time()

    logger.info(f"Time taken to query vector store: {t2 - t1} seconds")

    return references

@app.route('/generate_post', methods=['POST'])
def generate_post():
    data = request.get_json()
    
    user_prompt = data.get('user_prompt', '')
    references = data.get('references', {})
    list_authors = data.get('list_authors', [])
    social_platform = data.get('social_platform', '')

    post_of_author = []
    post_styles = []
    lst_emojis = []

    start_time = time.time()

    if social_platform.lower() == 'twitter':
        table = f'data_{vector_store.table_name}'

        step2_time = time.time()

        post_of_author = db.query_post_of_author(table, list_authors)
        if post_of_author:
            post_of_author = post_of_author[:2]
        else:
            post_of_author = []

        step3_time = time.time()
        logger.info(f"Time for querying posts of authors (Twitter): {step3_time - step2_time} seconds")
            
    elif social_platform.lower() == 'telegram':
        table = f'data_{vector_store_v2.table_name}'

        step2_time = time.time()

        post_of_author = db.query_post_of_author(table, list_authors)
        if post_of_author:
            post_of_author = post_of_author[:2]
        else:
            post_of_author = []

        step3_time = time.time()
        logger.info(f"Time for querying posts of authors (Telegram): {step3_time - step2_time} seconds")

    for key, value in references.items():
        values = emoji.emoji_list(value)
        for i in values:
            lst_emojis.append(i.get('emoji'))
    
    for i in post_of_author:
        values = emoji.emoji_list(i)
        for j in values:
            lst_emojis.append(j.get('emoji'))
    
    # Remove duplicate emojis
    lst_emojis = list(set(lst_emojis))

    for value in post_of_author:
        for text in value:
            post_styles.append(text)

    rag_prompt = RAGPrompt(
        user_order=user_prompt,
        references=references,
        lst_emojis=lst_emojis,
        social_platform=social_platform,
        post_of_author=post_styles
    ).prompt

    step4_time = time.time()
    output_post = llm.stream_chat(rag_prompt)
    generated_post = "".join([i.delta for i in output_post])
    step5_time = time.time()

    logger.info(f"Time for generating post: {step5_time - step4_time} seconds")
    
    generated_post_v2 = clean_generated_content(content=generated_post)

    end_time = time.time()
    logger.info(f"Total time for generating post process: {end_time - start_time} seconds")

    return generated_post_v2

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1201))
    print(port)
    app.run(host='0.0.0.0', port=port, debug=True)