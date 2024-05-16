import time
from pymongo import MongoClient, UpdateOne
from config import MongoDBConfig
from constant.time_constant import TimeConstants
from utils.dict_utils import flatten_dict, delete_none
from utils.logger_utils import get_logger

WALLETS_COL = 'depositWallets'

logger = get_logger('MongoDB')

class MongoDB:
    def __init__(self, connection_url=None, chain_id: str = ""):
        if not connection_url:
            connection_url = MongoDBConfig.CONNECTION_URL
        

        self.previous_3days = int(time.time() -TimeConstants.DAYS_3)

        self.connection_url = connection_url.split('@')[-1]
        self.connection = MongoClient(connection_url)

        self._db = self.connection[MongoDBConfig.DATABASE]
        self.lp_tokens_col = self._db['lpTokens']
        self._deposit_wallets_col = self._db['depositWallets']
        # self.wallets_col = self._db[WALLETS_COL]
        self._groups_col = self._db['groups']

        self._deposit_users_col = self._db['depositUsers']
        self._user_deposits_col = self._db['userDeposits']

        self._transactions_col = self._db[f'{chain_id}_transactions']
        self._token_transfers_col = self._db['token_transfers']


    #######################
    #       Generals      #
    #######################

    def count_documents(self, col_name):
        return self._db[col_name].estimated_document_count()

    def get_documents(self, col_name: str, skip: int, limit: int):
        return self._db[col_name].find({}).skip(skip).limit(limit)

    def get_documents_by_ids(self, col_name: str, ids: list):
        return self._db[col_name].find({'_id': {'$in': ids}})

    #######################
    #   Deposit - Users   #
    #######################

    def update_data(self, name, data):
        bulk_updates = [
            UpdateOne({'_id': datum['_id']}, {'$set': datum}, upsert=True
            )
            for datum in data
       ]
        self._db[f"{name}"].bulk_write(bulk_updates)

    def get_latest_tweets(self):
        data = self._db['tweets'].find({'timestamp':{'$gte':self.previous_3days}})
        data_lst = []
        for da in data:
            da_dct ={}
            if 'keyWords' in da:
                da_dct['_id'] = da['_id']
                da_dct['authorName'] = da['authorName']
                da_dct['timestamp'] =da['timestamp']
                da_dct['keyWords'] = da['keyWords']
                data_lst.append(da_dct)
        return data_lst


    
    def get_deposit_number_of_users(self, skip: int=0, limit: int=1):
        pipeline =  [
            {
                '$project': {
                    # 'chainId': '$chainId', 
                    # 'address': '$address', 
                    'numberOfUsers': {
                        '$size': '$userWallets'
                    }
                }
            }
        ]
        if skip:
            pipeline.append({
                    '$skip': skip
            })
        if limit:
            pipeline.append({
                    '$limit': limit
            })
        return self._deposit_users_col.aggregate(pipeline=pipeline)
    
    def get_deposit_wallet_by_users(self, chain_id, addresses):
        _ids = [f'{chain_id}_{address}' for address in addresses]
        _filter = {
            '_id': {'$in': _ids}
        }
        _projection = {
            '_id': 1,
            'depositWallets': 1,
            'address': 1
        }
        return self._user_deposits_col.find(_filter)
    
    @staticmethod
    def create_update_doc(document, keep_none=False, merge=True, shard_key=None):
        unset, set_, add_to_set = [], [], []
        if not keep_none:
            doc = flatten_dict(document)
            for key, value in doc.items():
                if value is None:
                    tmp = {
                        "_id": document["_id"],
                        key: ""
                    }
                    if shard_key:
                        tmp[shard_key] = document[shard_key]
                    unset.append(tmp)
                    continue
                if not merge:
                    continue
                if isinstance(value, list):
                    tmp = {
                        "_id": document["_id"],
                        key: {"$each": [i for i in value if i]}
                    }
                    if shard_key:
                        tmp[shard_key] = document[shard_key]
                    add_to_set.append(tmp)
                else:
                    tmp = {
                        "_id": document["_id"],
                        key: value
                    }
                    if shard_key:
                        tmp[shard_key] = document[shard_key]
                    set_.append(tmp)

        if not merge:
            if keep_none:
                set_.append(document)
            else:
                set_.append(delete_none(document))

        return unset, set_, add_to_set

    def update_docs(self, collection_name, data, keep_none=False, merge=True, shard_key=None, flatten=True):
        """If merge is set to True => sub-dictionaries are merged instead of overwritten"""
        try:
            col = self._db[collection_name]
            # col.insert_many(data, overwrite=True, overwrite_mode='update', keep_none=keep_none, merge=merge)
            bulk_operations = []
            if not flatten:
                if not shard_key:
                    bulk_operations = [UpdateOne({"_id": item["_id"]}, {"$set": item}, upsert=True) for item in data]
                else:
                    bulk_operations = [UpdateOne({"_id": item["_id"], shard_key: item[shard_key]}, {"$set": item}, upsert=True) for item in data]
                col.bulk_write(bulk_operations)
                return
            
            for document in data:
                unset, set_, add_to_set = self.create_update_doc(document, keep_none, merge, shard_key)
                if not shard_key:
                    bulk_operations += [
                        UpdateOne({"_id": item["_id"]},
                                  {"$unset": {key: value for key, value in item.items() if key != "_id"}}, upsert=True)
                        for item in unset]
                    bulk_operations += [
                        UpdateOne({"_id": item["_id"]},
                                  {"$set": {key: value for key, value in item.items() if key != "_id"}}, upsert=True)
                        for item in set_]
                    bulk_operations += [
                        UpdateOne({"_id": item["_id"]},
                                  {"$addToSet": {key: value for key, value in item.items() if key != "_id"}},
                                  upsert=True)
                        for item in add_to_set]
                if shard_key:
                    keys = ["_id", shard_key]
                    bulk_operations += [
                        UpdateOne({"_id": item["_id"], shard_key: item[shard_key]},
                                  {"$unset": {key: value for key, value in item.items() if key not in keys}},
                                  upsert=True)
                        for item in unset]
                    bulk_operations += [
                        UpdateOne({"_id": item["_id"], shard_key: item[shard_key]},
                                  {"$set": {key: value for key, value in item.items() if key not in keys}}, upsert=True)
                        for item in set_]
                    bulk_operations += [
                        UpdateOne({"_id": item["_id"], shard_key: item[shard_key]},
                                  {"$addToSet": {key: value for key, value in item.items() if key not in keys}},
                                  upsert=True)
                        for item in add_to_set]
            col.bulk_write(bulk_operations)
        except Exception as ex:
            logger.exception(ex)

