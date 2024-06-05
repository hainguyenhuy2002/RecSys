import os
import re
import emoji
from flasgger import Swagger
from flask_cors import CORS
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from databases.postgresql import PostgresDB
from models.embedding_models import EmbeddingModel
from models.embedding_models import LargeLanguageModel
from services.tweet_vector_query_service import tweet_vector_query
from utils.logger_utils import get_logger
from constant.prompt import RAGPrompt
from config import EmbeddingModelConfig, LLMModelConfig
import time

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)

model = EmbeddingModel()._embed_model
vector_store=PostgresDB().vector_store
vector_store_v2=PostgresDB().vector_store_v2
db = PostgresDB()
llm = LargeLanguageModel()._embed_model

logger = get_logger("PostGenerationService")

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


class PostGenerationWithRAG(Resource):
    def get(self):
        return """ Welcome to post generation task, I am is LLM and I'll help to generate your marketing post """ , 200
    
    def post(self):
        try:
            user_input = request.get_json()
            
            list_authors = user_input['list_authors']
            keywords = user_input['keyWords']
            social_platform = user_input['socialPlatform']
            
            references = {}
            post_of_author = []
            post_styles = []
            lst_emojis = []

            start_time = time.time()

            if social_platform.lower() == 'twitter':
                simi_tweets = tweet_vector_query(
                    embed_model=model,
                    vector_store=vector_store,
                    input_keyword=keywords,
                    top_simi=10)
                
                step1_time = time.time()
                logger.info(f"Time for tweet_vector_query (Twitter): {step1_time - start_time} seconds")
                
                references = {}
                for key, value in simi_tweets.items():
                    if len(value) < 350:
                        references[key] = value
                    else:
                        continue
                
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
                references = tweet_vector_query(
                    embed_model=model,
                    vector_store=vector_store_v2,
                    input_keyword=keywords,
                    top_simi=10)
                
                step1_time = time.time()
                logger.info(f"Time for tweet_vector_query (Telegram): {step1_time - start_time} seconds")
                
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
        
            step4_time = time.time()
        
            if ('rag' in user_input):
                return  references, 201
            else:
                rag_prompt = RAGPrompt(
                    user_order=keywords,
                    references=references,
                    lst_emojis=lst_emojis,
                    social_platform=social_platform,
                    post_of_author=post_styles
                ).prompt
         
                output_post = llm.stream_chat(rag_prompt)
                generated_post = "".join([response.delta for response in output_post])
                step5_time = time.time()

                logger.info(f"Time for generating post: {step5_time - step4_time} seconds")

                generated_post_v2 = clean_generated_content(generated_post)

                end_time = time.time()
                logger.info(f"Total time for generating post: {end_time - start_time} seconds")

                return generated_post_v2, 201
            
        except Exception as error:
           return {'error': error}

api.add_resource(PostGenerationWithRAG,'/genpost')

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