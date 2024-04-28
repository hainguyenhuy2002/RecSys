import pandas as pd
import numpy as np
from llama_index.core.schema import TextNode
from databases.mongodb import MongoDB
from databases.postgresql import PostgresDB
from models.embedding_models import EmbedingModel

def upload_vector_db():
    embed_model = EmbedingModel()
    mongo_db = MongoDB()
    posgre_db = PostgresDB()

    df_tweet = mongo_db.get_tweet()
    nodes = []
    for index, row in df_tweet.iterrows():
        node = TextNode(text=row['content'], id_=f"{row['authorName']}_{row['timestamp']}")
        nodes.append(node)

    for node in nodes:
        node_embedding = embed_model.get_text_embedding(
            node.get_content(metadata_mode="all")
        )
        node.embedding = node_embedding
    posgre_db.upload_vector_db(vector_data=nodes)