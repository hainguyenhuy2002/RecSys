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
from jobs.cli_job import CLIJob
from utils.logger_utils import get_logger
from utils.preprocess_utils import get_lemma
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-i', '--interval', default=TimeConstants.A_DAY, type=int, help='Sleep time')

def upload_vector_db(interval):
    job = UploadVectorDB(interval=interval)
    job.run()

def configure_loggers():
    logg = get_logger("Embedding storage")
    progress_logger = logging.getLogger('ProgressLogger')
    progress_logger.setLevel(logging.WARNING)
    execute_logger = logging.getLogger('Time Execute')
    execute_logger.setLevel(logging.WARNING)
    return logg, progress_logger, execute_logger

class UploadVectorDB(CLIJob):
    def __init__(self, interval=None, end_timestamp=None, retry=True):
        super().__init__(interval, end_timestamp, retry)
        self.logg, self.progress_logger, self.execute_logger = configure_loggers()

    def _pre_start(self):
        self.logg.info("Start to connect model and database ...")

    def _start(self):
        ...

    def _execute(self, *args, **kwargs):
        self.upload_vector_database_twitter()
        # self.upload_vector_database_discord()

    def upload_vector_database_twitter(self):
        embed_model = EmbeddingModel()
        mongo_db = MongoDB()
        posgre_db = PostgresDB()

        self.logg.info("Start to get tweet data ...")

        df_tweet = mongo_db.get_tweet()

        self.logg.info(f"Successfully get tweet data: {len(df_tweet)} tweets")

        self.logg.info("Start to process tweet data ...")
        df_tweet['tweet_length'] = df_tweet['content'].apply(len)
        df_tweet_filter =df_tweet[(df_tweet['tweet_length']>200)].reset_index(drop=True)        
        nodes = []
        nodes_with_timestamp = {}

        for index, row in df_tweet_filter.iterrows():
            node = TextNode(text=row['content'], id_=f"{row['authorName']}_{row['_id']}", )
            nodes.append(node)
            nodes_with_timestamp[node.id_] = row['timestamp']

        for node in nodes:
            node_embedding = embed_model._embed_model.get_text_embedding(
                get_lemma(node.get_content(metadata_mode="all"))
            )
            node.embedding = node_embedding
            node.metadata = node_to_metadata_dict(node)
 
        self.logg.info("Successfully process tweet data ...")
        self.logg.info("Start to upload tweet data ...")

        posgre_db.upsert_nodes(nodes, nodes_with_timestamp)
        self.logg.info("Successfully upload tweet data ...")

    def upload_vector_database_tele(self):
        embed_model = EmbeddingModel()
        mongo_db = MongoDB()
        posgre_db = PostgresDB()

        self.logg.info("Start to get tweet data ...")

        df_tele = mongo_db.get_tele()

        self.logg.info(f"Successfully get tweet data: {len(df_tele)} messages")

        self.logg.info("Start to process tweet data ...")
        df_tele['message_length'] = df_tele['message'].apply(len)
        df_tele_filter =df_tele[(df_tele['message_length']>200)].reset_index(drop=True)        
        nodes = []
        nodes_with_timestamp = {}

        for index, row in df_tele_filter.iterrows():
            node = TextNode(text=row['message'], id_=f"{row['_id']}", )
            nodes.append(node)
            nodes_with_timestamp[node.id_] = row['timestamp']
 
        for node in nodes:
            node_embedding = embed_model._embed_model.get_text_embedding(
                get_lemma(node.get_content(metadata_mode="all"))
            )
            node.embedding = node_embedding
            node.metadata = node_to_metadata_dict(node)
 
        self.logg.info("Successfully process tweet data ...")
        self.logg.info("Start to upload tweet data ...")

        posgre_db.upsert_nodes(nodes, nodes_with_timestamp)
        self.logg.info("Successfully upload tweet data ...")