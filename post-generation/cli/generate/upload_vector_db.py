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
from services.upload_vector_database import UploadVectorDB
from config import PostgresRAGDBConfig
from utils.logger_utils import get_logger
from utils.preprocess_utils import get_lemma
from langdetect import detect

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-i', '--interval', default=TimeConstants.A_DAY, type=int, help='Sleep time')
@click.option('-b', '--batch-size', default=500, type=int)
@click.option('-w', '--max-workers', default=4, show_default=True, type=int,
              help='The number of workers')
@click.option('-s', '--social', default=['twitter', 'telegram'], show_default=True, type=str, help='social type')

def upload_vector_db(interval, batch_size, max_workers, social):
    jobb = UploadVectorDataBase(interval=interval, batch_size=batch_size, max_workers=max_workers, social=social)
    jobb.run()

def configure_loggers():
    logg = get_logger("Embedding storage")
    progress_logger = logging.getLogger('ProgressLogger')
    progress_logger.setLevel(logging.WARNING)
    execute_logger = logging.getLogger('Time Execute')
    execute_logger.setLevel(logging.WARNING)
    return logg, progress_logger, execute_logger

class UploadVectorDataBase(CLIJob):
    def __init__(self, interval=None, end_timestamp=None, retry=True, batch_size=None, max_workers=None, social=None):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.social = social
        super().__init__(interval, end_timestamp, retry)
        self.logg, self.progress_logger, self.execute_logger = configure_loggers()
      
    def _pre_start(self):
        self.logg.info("Start to connect model and database ...")

    def _execute(self, *args, **kwargs):
        if self.social == 'twitter':
            self.upload_vector_db_tweet()
        elif self.social == 'telegram':
            self.upload_vector_db_telegram()
        else:
            self.upload_vector_db_tweet()
            self.upload_vector_db_telegram()

    def upload_vector_db_tweet(self):
        embed_model = EmbeddingModel()
        mongo_db = MongoDB()
        posgre_db = PostgresDB()

        posgre_table = f"data_{PostgresRAGDBConfig.RAG_TABLE}"

        batch_size = self.batch_size
        max_workers = self.max_workers
        social = 'twitter'

        self.logg.info("Start to get tweet data ...")

        df_tweet = mongo_db.get_tweet()

        self.logg.info(f"Successfully get tweet data: {len(df_tweet)} tweets")
        self.logg.info("Start to process tweet data ...")

        df_tweet['tweet_length'] = df_tweet['content'].apply(len)
        df_tweet_filter =df_tweet[(df_tweet['tweet_length']>200)].reset_index(drop=True)
        # Get only English tweets
        try:
            df_tweet_filter['lang'] = df_tweet_filter['content'].apply(detect)
            df_tweet_filter = df_tweet_filter[df_tweet_filter['lang'] == 'en']     
        except:
            pass   

        index_list = list(range(batch_size, len(df_tweet_filter), batch_size))
        index_list.append(len(df_tweet_filter))

        job = UploadVectorDB(embed_model=embed_model, importer=posgre_db, exporter=posgre_table, index_lst=index_list, df_filter=df_tweet_filter, batch_size=batch_size, max_workers=max_workers, social=social)
        job.run()
        self.logg.info("Successfully upload tweet data ...")

    def upload_vector_db_telegram(self):
        embed_model = EmbeddingModel()
        mongo_db = MongoDB()
        posgre_db = PostgresDB()

        posgre_table = f"data_{PostgresRAGDBConfig.RAG_TABLE_V2}"

        batch_size = self.batch_size
        max_workers = self.max_workers
        social = 'telegram'

        self.logg.info("Start to get telegram data ...")

        df_tele = mongo_db.get_tele()

        self.logg.info(f"Successfully get telegram data: {len(df_tele)} messages")
        self.logg.info("Start to process telegram data ...")

        df_tele['tweet_length'] = df_tele['content'].apply(len)
        df_tele_filter =df_tele[(df_tele['tweet_length']>200)].reset_index(drop=True)
        # Get only English tweets
        try:
            df_tele_filter['lang'] = df_tele_filter['content'].apply(detect)
            df_tele_filter = df_tele_filter[df_tele_filter['lang'] == 'en']     
        except:
            pass   

        index_list = list(range(batch_size, len(df_tele_filter), batch_size))
        index_list.append(len(df_tele_filter))

        job = UploadVectorDB(embed_model=embed_model, importer=posgre_db, exporter=posgre_table, index_lst=index_list, df_filter=df_tele_filter, batch_size=batch_size, max_workers=max_workers, social=social)
        job.run()
        self.logg.info("Successfully upload telegram data ...")
