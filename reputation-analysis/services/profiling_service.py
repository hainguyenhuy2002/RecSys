import numpy as np 
import pandas as pd 
from multithread_processing.base_job import BaseJob
from databases.mongodb_main import MongoDBMain


    

class GetTransactionInfo(BaseJob):
    def __init__(self, chain, collections, historical_token_price, wallets_list: list, reputation_df: pd.DataFrame, filename: str, start_date, end_date,
                 max_workers= 4, batch_size=500):
        
        mongo = MongoDBMain(chain=chain)
        self.transac_collection = mongo._db[collections]        
        self.transaction_info = list()
        self.transfer_info = list()
        self.filename = filename
        self.start_date = start_date
        self.end_date = end_date
        self.historical_token_price = historical_token_price
        self.reputation_df = reputation_df
        super().__init__(work_iterable=wallets_list,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        df_list = list()
        cursor =self.transac_collection.find({"block_timestamp" : {"$gte": self.start_date, "$lte": self.end_date},'from_address': {'$in': works}},{'from_address':1, 'to_address':1, 'value':1, 'block_timestamp':1,'transaction_type':1})
        for doc in cursor:
            single_transaction_info = dict(doc) 
            if single_transaction_info['value'] == '0':
                continue
            else:
                round_timestamp = (single_transaction_info['block_timestamp']  - single_transaction_info['block_timestamp']  % 86400) *1000
                single_transaction_info['valueInUSD'] = int(single_transaction_info['value']) * self.historical_token_price['ethereum'][round_timestamp]
                df_list.append(single_transaction_info)    

        df_concat = pd.DataFrame(df_list)        
        info_wallet = df_concat.groupby(['from_address', 'to_address']).agg({"block_timestamp":tuple, "valueInUSD": np.sum}).reset_index().rename(columns={"from_address": "wallet","to_address":"sending_wallet"})
        info_wallet = info_wallet.merge(self.reputation_df[['wallet', 'NumberOfTokensBorrow',	'NumberOfTokensDeposit', 'NumberOfTokensHold', 'totalBorrowInUSD', 'totalDepositInUSD',	'totalHoldInUSD', 'score']], on='wallet', how='inner')
        self.transaction_info.append(info_wallet)
        
    def _end(self):
        super()._end()
        df = pd.concat(self.transaction_info, ignore_index=True)
        #return df
        df.to_csv(self.filename, index=False)
