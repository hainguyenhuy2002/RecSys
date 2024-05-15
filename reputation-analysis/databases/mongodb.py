from pymongo import MongoClient, UpdateOne, InsertOne

from config import MongoDBConfig

WALLETS_COL = 'depositWallets'


class MongoDB:
    def __init__(self, connection_url=None, chain_id: str = ""):
        if not connection_url:
            connection_url = MongoDBConfig.CONNECTION_URL

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
