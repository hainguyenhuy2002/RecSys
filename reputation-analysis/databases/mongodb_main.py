from typing import List, Dict
from pymongo import MongoClient

from config import MongoDBMainConfig
from utils.logger_utils import get_logger

logger = get_logger('MongoDB Entity')


class MongoDBMain:
    def __init__(self, connection_url=None, chain=None):
        if not connection_url:
            connection_url = MongoDBMainConfig.CONNECTION_URL
        self.connection = MongoClient(connection_url)
        if chain == 'bsc':
            database = 'blockchain_etl'
        else:
            database = f'{chain}_blockchain_etl'
        self._db = self.connection[database]
        self._transaction = self._db['transactions']

