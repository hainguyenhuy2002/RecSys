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
@click.option('-s', '--social', default=['twitter', 'telegram'], show_default=True, type=str, help='social type')

def prune_vector_db(interval, social):
    job = PruneVectorDataBase(interval=interval, social=social)
    job.run()


def configure_loggers():
    logg = get_logger("PruneVectorDB")
    progress_logger = logging.getLogger('ProgressLogger')
    progress_logger.setLevel(logging.WARNING)
    execute_logger = logging.getLogger('Time Execute')
    execute_logger.setLevel(logging.WARNING)
    return logg, progress_logger, execute_logger


class PruneVectorDataBase(CLIJob):
    def __init__(self, interval=None, end_timestamp=None, retry=True, social=None):
        super().__init__(interval, end_timestamp, retry)
        self.social = social
        self.logg, self.progress_logger, self.execute_logger = configure_loggers()
       
    def _pre_start(self):
        self.logg.info("Start to connect database ...")

    def _execute(self, *args, **kwargs):
        if self.social == 'twitter':
            self.prune_vector_db_tweet()
        elif self.social == 'telegram':
            self.prune_vector_db_telegram()

    def prune_vector_db_tweet(self):
        posgre_db = PostgresDB()

        self.logg.info("Start to prune vector db tweet ...")
        posgre_db.prune_vector_db_tweet()
        self.logg.info("End to prune vector db tweet ...")


    def prune_vector_db_telegram(self):
        posgre_db = PostgresDB()

        self.logg.info("Start to prune vector db telegram ...")
        posgre_db.prune_vector_db_telegram()
        self.logg.info("End to prune vector db telegram ...")