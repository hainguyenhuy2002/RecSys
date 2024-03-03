from typing import List, Dict
from pymongo import MongoClient
from constants.mongodb_main_constants import MongoMainCollections
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
        self._transaction = self._db[MongoMainCollections.transactions]
        self.block_collection = self._db[MongoMainCollections.blocks]

    def get_blocks_in_range(self, start_block, end_block,
                            projection: List = None):
        filter_ = {
            'number': {
                "$gte": start_block,
                "$lte": end_block
            }
        }
        if not projection:
            cursor = self.block_collection.find(filter_).batch_size(1000)
        else:
            cursor = self.block_collection.find(filter=filter_, projection=projection).batch_size(1000)
        return cursor

    def get_block_number_to_timestamp(self, start_block, end_block) -> Dict[int, int]:
        cursor = self.get_blocks_in_range(start_block=start_block, end_block=end_block,
                                          projection=['number', 'timestamp'])
        return {block['number']: block['timestamp'] for block in cursor}
