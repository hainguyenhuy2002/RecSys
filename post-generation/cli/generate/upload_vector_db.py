import click
import pandas as pd
import numpy as np
import time
import logging
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.utils import node_to_metadata_dict
from databases.mongodb import MongoDB
from databases.postgresql import PostgresDB
from models.embedding_models import EmbeddingModel
from constant.time_constant import TimeConstants
from services.cli_job import CLIJob
from utils.logger_utils import get_logger
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-i', '--interval', default=TimeConstants.A_DAY, type=int, help='Sleep time')

def upload_vector_db(interval):
    job = UploadVectorDB(interval=interval)
    job.run()

class UploadVectorDB(CLIJob):
    def __init__(self, interval=None, end_timestamp=None, retry=True):
        super().__init__(interval, end_timestamp, retry)

    def _pre_start(self):
        logg = get_logger("Embedding storage")
        logg.info("Start to connect model and database ...")

        progress_logger = logging.getLogger('ProgressLogger')
        progress_logger.setLevel(logging.WARNING)
        execute_logger = logging.getLogger('Time Execute')
        execute_logger.setLevel(logging.WARNING)

    def _start(self):
        ...

    def _execute(self, *args, **kwargs):
        self.upload_vector_database_twitter()
        # self.upload_vector_database_discord()

    def upload_vector_database_twitter(self):
        embed_model = EmbeddingModel()
        mongo_db = MongoDB()
        posgre_db = PostgresDB()

        df_tweet = mongo_db.get_tweet()
        
        nodes = []

        for index, row in df_tweet.iterrows():
            node = TextNode(text=row['content'], id_=f"{row['authorName']}_{row['_id']}", )
            nodes.append(node)

        for node in nodes:
            node_embedding = embed_model._embed_model.get_text_embedding(
                node.get_content(metadata_mode="all")
            )
            node.embedding = node_embedding
            node.metadata = node_to_metadata_dict(node)
            
        posgre_db.upsert_nodes(nodes)

    def upload_vector_database_discord(self):
        embed_model = EmbeddingModel()
        mongo_db = MongoDB()
        posgre_db = PostgresDB()

        df_message = mongo_db.get_message()
        nodes = []

        for index, row in df_message.iterrows():
            node = TextNode(text=row['content'], id_=row['_id'])
            nodes.append(node)
        
        for node in nodes:
            node_embedding = embed_model._embed_model.get_text_embedding(
                node.get_content(metadata_mode="all")
            )
            node.embedding = node_embedding
            node.metadata = node_to_metadata_dict(node)
            
        posgre_db.upsert_nodes(nodes)