import time
import pymongo

from typing import List, Dict
from pymongo import MongoClient
from constants.mongodb_main_constants import MongoMainCollections
from constants.time_constants import TimeConstants
from config import MongoDBMainConfig
from utils.logger_utils import get_logger, write_file


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
        
    def get_transaction_info(self, start_date, end_date, direction, opposite_direction, special_addresses, addresses, price_history):
        addresses_info = list()
        try:
            query = {"block_timestamp" : {"$gte": start_date, "$lte": end_date},f'{direction}_address': {'$in': addresses}, 
                                                    f'{opposite_direction}_address':{'$nin': special_addresses}}
            transactions_data =self._transaction.find(query,{'from_address':1, 'to_address':1, 'value':1, 'block_timestamp':1})
            for transaction in transactions_data:
                single_transaction_info = dict(transaction) 
                if single_transaction_info['value'] == '0':
                    continue
                else:
                    round_timestamp = ((single_transaction_info['block_timestamp']  - single_transaction_info['block_timestamp']  % 86400))*1000  #change to timestamp daily
                    single_transaction_info['valueInUSD'] = (int(single_transaction_info['value']) * price_history[f'{round_timestamp}']) /10**18
                    single_transaction_info['amount'] = int(single_transaction_info['value']) /10**18
                    addresses_info.append(single_transaction_info)    
        except Exception as e:
            log =get_logger("Oh no getting an error in the query Mongo task")
            write_file('mongo_query', 'failed_addresses', addresses)
            log.info(e)
            addresses_info = list()
        return addresses_info

    def get_largest_block(self):
        uppper_time =int(time.time()) - TimeConstants.A_DAY #17s/05/2024
        query = {'timestamp':{'$lte':uppper_time}}
        projection =  {'timestamp':1,'number':1}
        cursor = self._db.blocks.find(query, 
                                      projection=projection) \
                                        .sort('timestamp',pymongo.DESCENDING) \
                                        .limit(1)
        return {block['number']: block['timestamp'] for block in cursor}

    def get_previous_3month_block(self):
        time_now = int(time.time()) - TimeConstants.A_DAY
        lower_time = int(time_now) - TimeConstants.MONTHS_3
        query = {'timestamp':{'$gte':lower_time}}
        projection =  {'timestamp':1,'number':1}
        cursor = self._db.blocks.find(filter=query,
                                      projection=projection). \
                                        sort('timestamp',pymongo.ASCENDING).limit(1)
        return {block['number']: block['timestamp'] for block in cursor}

    def get_previous_1month_block(self):
        time_now = int(time.time()) - TimeConstants.A_DAY
        lower_time = int(time_now) - TimeConstants.DAYS_31
        query = {'timestamp':{'$gte':lower_time}}
        projection =  {'timestamp':1,'number':1}
        cursor = self._db.blocks.find(filter=query,
                                      projection=projection) \
                                        .sort('timestamp',pymongo.ASCENDING) \
                                        .limit(1)
        return {block['number']: block['timestamp'] for block in cursor}
    
    def get_previous_2day_block(self):
        time_now = int(time.time()) - TimeConstants.A_DAY
        lower_time = int(time_now) - TimeConstants.DAYS_2
        query = {'timestamp':{'$gte':lower_time}}
        projection =  {'timestamp':1,'number':1}
        cursor = self._db.blocks.find(filter=query,
                                      projection=projection) \
                                        .sort('timestamp',pymongo.ASCENDING) \
                                        .limit(1)
        return {block['number']: block['timestamp'] for block in cursor}

    def get_block_number_to_timestamp(self, start_block, end_block) -> Dict[int, int]:
        cursor = self.get_blocks_in_range(start_block=start_block, end_block=end_block,
                                          projection=['number', 'timestamp'])
        return {block['number']: block['timestamp'] for block in cursor}

