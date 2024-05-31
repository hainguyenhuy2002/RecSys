import os
import re
import emoji
from flasgger import Swagger
from flask_cors import CORS
from flask import Flask, request
from flask_restful import Resource, Api
from databases.postgresql import PostgresDB
from models.embedding_models import EmbeddingModel
from models.embedding_models import LargeLanguageModel
from services.tweet_vector_query_service import tweet_vector_query
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
            
            author = user_input['author']
            keywords = user_input['keyWords']
            social_platform = user_input['socialPlatform']
            
            if social_platform.lower() == 'twitter':
                simi_tweets = tweet_vector_query(
                    EmbedModel=model,
                    vector_store=vector_store,
                    input=keywords,top_simi=20)
                
                # Filter the query result which have the length of content < 350
                references = {}
                for key, value in simi_tweets.items():
                    if len(value) < 350:
                        references[key] = value
                    else:
                        continue
                
                table = f'data_{vector_store.table_name}'

                try:
                    post_of_author = db.query_post_of_author(table, author)
                except Exception as error:
                    post_of_author = []

                try:
                    if len(post_of_author) > 10:
                        post_of_author = post_of_author[:10]
                    else:
                        post_of_author = post_of_author
                except Exception as error:
                    post_of_author = []
                
            if social_platform.lower() == 'telegram':
                references = tweet_vector_query(
                    EmbedModel=model,
                    vector_store=vector_store_v2,
                    input=keywords,top_simi=20)
                
                table = f'data_{vector_store_v2.table_name}'

                try:
                    post_of_author = db.query_post_of_author(table, author)
                except Exception as error:
                    post_of_author = []
                
                try:
                    if len(post_of_author) > 10:
                        post_of_author = post_of_author[:10]
                    else:
                        post_of_author = post_of_author
                except Exception as error:
                    post_of_author = []

            # Get emojis from references and post of author
            lst_emojis = []
            for key, value in references.items():
                values = emoji.emoji_list(value)
                for i in values:
                    lst_emojis.append(i.get('emoji'))
            
            for i in post_of_author:
                values = emoji.emoji_list(i)
                for i in values:
                    lst_emojis.append(i.get('emoji'))
            
            # Remove duplicate emojis
            lst_emojis = list(set(lst_emojis))

            post_styles = []
            try:
                for value in post_of_author:    
                    for text in value:
                        post_styles.append(text)
            except Exception as error:
                post_styles = []
        
            if ('rag' in user_input):
                return  references, 201
            else:
                ragprompt = RAGPrompt(
                    user_order=keywords,
                    references=references,
                    lst_emojis=lst_emojis,
                    social_platform=social_platform,
                    post_of_author=post_styles
                ).prompt
         
                # output_post = llm.stream_chat(ragprompt)
                # generated_post = "".join([response.delta for response in output_post])
                output_post = llm.chat.completions.create(
                    messages=ragprompt, 
                    model=LLMModelConfig.MODEL_NAME, 
                    max_tokens=LLMModelConfig.MODEL_KWARGS['max_length'], 
                    temperature=LLMModelConfig.MODEL_KWARGS['temperature'],
                    top_p=LLMModelConfig.MODEL_KWARGS['top_p']
                )
                generated_post = output_post.choices[0].message.content
                generated_post_v2 = clean_generated_content(generated_post)

                return generated_post_v2, 201
            
        except Exception as error:
           return {'error': error}

api.add_resource(PostGenerationWithRAG,'/genpost')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 1201))
    print(port)
    app.run(host='0.0.0.0', port=port, debug=True)