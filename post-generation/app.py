import os
import re
from flasgger import Swagger
from flask_cors import CORS
from flask import Flask, request
from flask_restful import Resource, Api
from databases.postgresql import PostgresDB
from models.embedding_models import EmbeddingModel
from models.embedding_models import LargeLanguageModel
from services.tweet_vector_query_service import tweet_vector_query
from constant.prompt import RAGPrompt, NormalPrompt

app = Flask(__name__)
api = Api(app)
swagger = Swagger(app)

model = EmbeddingModel()._embed_model
vector_store=PostgresDB().vector_store
vector_store_v2=PostgresDB().vector_store_v2
llm = LargeLanguageModel()._embed_model

def clean_generated_content(content):
    max_hashtags = 5
    # Remove system notes or character count indicators enclosed in any brackets or common phrases
    patterns_to_remove = [
        r'<<.*?>>',   
        r'<.*?>',             # Anything between << and >>
        r'\([^)]*\)',              # Anything between ( and )
        r'\[[^\]]*\]',             # Anything between [ and ]
        r'I hope this.*?', # Common phrase for notes
        r'.*?Note.*?|.*?note.\*?|.*?Sure.*?\n\n|.*?sure.*?\n\n',
        r'.*?Please let me know.*?\n\n', # any sentence containing "Please let me know"
        r".*?Here's.*?\n\n", # any sentence containing "Here's"
        r".*?Here are.*?\n\n", # any sentence containing "Here are"
        r".*?Here is.*?\n\n", # any sentence containing "Here is"
        r"Here is the final version of the post:\n\n", # any sentence containing "Here is the final version of the post:"
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Normalize whitespace, keeping double newlines
    content = re.sub(r'[ \t]+', ' ', content)
    # content = re.sub(r'\n\n\n', '\n\n', content)
    content = content.strip()

    hashtags = re.findall(r'#\w+', content)
    if len(hashtags) > max_hashtags:
        content = re.sub(r'#\w+', '', content)
        content += ' ' + ' '.join(hashtags[:max_hashtags])
    
    return content

class PostGenerationWithRAG(Resource):
    def get(self):
        return """ Welcome to post generation task, I am is LLM and I'll help to generate your marketing post """ , 200
    def post(self):
        #try:
            user_input = request.get_json()
        
            keywords = user_input['keyWords']
            social_platform = user_input['socialPlatform']
            
            if social_platform.lower() == 'twitter':
                simi_tweets, lst_emojis = tweet_vector_query(
                    EmbedModel=model,
                    vector_store=vector_store,
                    input=keywords,top_simi=20)
                
            if social_platform.lower() == 'telegram':
                simi_tweets, lst_emojis = tweet_vector_query(
                    EmbedModel=model,
                    vector_store=vector_store_v2,
                    input=keywords,top_simi=20)
            
            if ('rag' in user_input):
                return  simi_tweets, 201
            else:
                ragprompt = RAGPrompt(
                    user_order=keywords,
                    references=simi_tweets,
                    lst_emojis=lst_emojis,
                    social_platform=social_platform
                ).prompt
         
                output_post = llm.stream_chat(ragprompt)
                generated_post = "".join([response.delta for response in output_post])

                normprompt = NormalPrompt(
                    first_reponse=generated_post,
                    social_platform=social_platform
                ).prompt
                output_post_v2 = llm.stream_chat(normprompt)
                generated_post_v2 = "".join([response.delta for response in output_post_v2])
                generated_post_v2 = clean_generated_content(generated_post)

                return generated_post_v2, 201
        #except Exception as error:
         #   return {'error': error}
        

api.add_resource(PostGenerationWithRAG,'/genpost')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1201))
    print(port)
    app.run(host='0.0.0.0', port=port, debug=True)