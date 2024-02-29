import numpy as np 
import pandas as pd 
from multithread_processing.base_job import BaseJob
from databases.mongodb_main import MongoDBMain
from utils.logger_utils import get_logger
from typing import List
from constants.network_constants import Chains

class GetTransactionInfo(BaseJob):
    def __init__(self, chain, mongo_transaction, postgres, historical_token_price, block_timestamp_mappings, wallets_list: list, reputation_df: pd.DataFrame, direction, filename: str, start_date, end_date, start_block, end_block,
                 max_workers= 4, batch_size=500, sources: List[str] = None):
        self.logg1 = get_logger("Start to query and preprocess transaction information of reputation addresses!!!")

        self.transaction_info = list()
        self.transfer_info = list()
    
        self.chain = chain
        self.mongo_transaction = mongo_transaction
        self.postgres = postgres
        self.historical_token_price = historical_token_price
        self.block_timestamp_mappings = block_timestamp_mappings
        self.reputation_df = reputation_df

        self.start_date = start_date
        self.end_date = end_date
        self.start_block = start_block
        self.end_block = end_block
        if direction == 'sending':
            self.direction = 'from'
        elif direction == 'receiving':
            self.direction = 'to'
        self.filename = filename
    
        if not sources:
            sources = ['mongo', 'postgres']
        self.sources = sources
        self.chain_id = Chains.mapping[chain]

        super().__init__(work_iterable=wallets_list,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        for source in self.sources:
            if source =='mongo':
                self._wallet_transaction_info(works=works, historical_token_price=self.historical_token_price, direction= self.direction, start_date= self.start_date, end_date= self.end_date)
            elif source =='postgres':
                self._wallet_transfer_info(works=works, block_timestamp_mappings= self.block_timestamp_mappings, direction= self.direction, chain_id= self.chain_id, start_block=self.start_block, end_block=self.end_block)

    def _wallet_transaction_info(self, works, historical_token_price, direction, start_date, end_date): 
        df_list = list()
          
        try:
            transactions_data =self.mongo_transaction.find({"block_timestamp" : {"$gte": start_date, "$lte": end_date},f'{direction}_address': {'$in': works}},{'from_address':1, 'to_address':1, 'value':1, 'block_timestamp':1})
            for transaction in transactions_data:
                single_transaction_info = dict(transaction) 
                if single_transaction_info['value'] == '0':
                    continue
                else:
                    round_timestamp = ((single_transaction_info['block_timestamp']  - single_transaction_info['block_timestamp']  % 86400) *1000)  #change to timestamp daily
                    single_transaction_info['valueInUSD'] = (int(single_transaction_info['value']) * historical_token_price['ethereum'][round_timestamp]) /10**12
                    df_list.append(single_transaction_info)    
        except Exception as e:
            self.logg1.info(e)
        if len(df_list) !=0:
            df_concat = pd.DataFrame(df_list)
            try:
                if direction == 'from':
                    wallet_transaction_info = df_concat.groupby(['from_address', 'to_address']).agg({"block_timestamp":tuple, "valueInUSD": ['sum', 'median']})
                    wallet_transaction_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transaction_info.columns]
                    wallet_transaction_info = wallet_transaction_info.reset_index().rename(columns={"from_address": "wallet","to_address":"sending_wallet"})

                elif direction == 'to':
                    wallet_transaction_info = df_concat.groupby(['from_address', 'to_address']).agg({"block_timestamp":tuple, "valueInUSD": ['sum', 'median']})
                    wallet_transaction_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transaction_info.columns]
                    wallet_transaction_info = wallet_transaction_info.reset_index().rename(columns={"to_address": "wallet","from_address":"receiving_wallet"})
                wallet_transaction_info = wallet_transaction_info.merge(self.reputation_df[['wallet', 'NumberOfTokensBorrow',	'NumberOfTokensDeposit', 
                                                                    'NumberOfTokensHold', 'totalBorrowInUSD', 'totalDepositInUSD',	'totalHoldInUSD', 'score']], on='wallet', how='inner')
                self.transaction_info.append(wallet_transaction_info)
            except Exception as e:
                self.logg1.info(e)   

    def _wallet_transfer_info(self, works, block_timestamp_mappings, direction, chain_id, start_block, end_block): 
        transfers_data = self.postgres.query_addresses(addresses=works, direction= direction, from_block=start_block,
                                                        to_block=end_block,
                                                        chain_id=chain_id)
        wallet_transfer = []
        fields_to_select =['contract_address', 'block_number', 'from_address', 'to_address', 'value']
        for row in transfers_data:
            new_row = row[:1] + (block_timestamp_mappings[row[1]],) +row[2:]
            wallet_transfer.append(dict(zip(fields_to_select, new_row)))
        wallet_transfer_info = pd.DataFrame(wallet_transfer)
        self.transfer_info.append((wallet_transfer_info))


    def _end(self):
        super()._end()
        transaction_df = pd.concat(self.transaction_info, ignore_index=True)
        transfer_df = pd.concat(self.transfer_info, ignore_index=True)
        #return df
        transaction_df.to_csv(self.filename, index=False)
        transfer_df.to_csv(self.transfer_info, index=False)
