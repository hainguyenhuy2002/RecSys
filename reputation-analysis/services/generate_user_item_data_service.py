import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Set, List
from multithread_processing.base_job import BaseJob
from utils.logger_utils import get_logger
from pymongo import MongoClient


def deposit_borrow_info(dictionary, timestamp):
    if (dictionary =={}) |(dictionary ==0):
        return 0
    elif not dictionary:
        return 0
    
    sub_dict = {key: value for key, value in dictionary.items() if (key <= timestamp)}  
    if sub_dict =={}:
        return 0
    return round(list(sub_dict.values())[-1], 2)


class GetUserItem(BaseJob):
    def __init__(self, mongo_klg, mongo_clt, index_lst, saving_path, direction, timestamp, contract_set, max_workers= 4, batch_size=500):
        """
        users - items:
        lending Contract will be users
        lending users will be items    
        
        """
        self.mongo_klg = mongo_klg
        self.mongo_clt = mongo_clt

        self.batch_size = batch_size
        self.saving_path = saving_path
        self.direction = direction
        self.str_timestamp = str(timestamp)
        self.timestamp = timestamp
        self.rows = []
        self.contract_set = contract_set
        self.lending_address_lst = []
        self.contract_address_lst = []
        super().__init__(work_iterable=index_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        if self.direction =='lendings':
            self._get_lending_user_items(works)
        if self.direction =='contracts':
            self._get_contract_user_items(works)

    def _get_lending_user_items(self, works):
        lending_user_rating_dict ={}
        lending_contract_lst =list()
        lending_user_lst = list()
        lending_rating_lst = list()
        cursor = self.mongo_klg._db['wallets'].find({'_id':{ '$in': works}},{'_id':1, 'lendings':1})
        balance_lst = ['_id','lendings']
        for lending_users in cursor:
            lending_balance =  {key: lending_users.get(key) for key in balance_lst}
            if (lending_balance['lendings'] != {})&(lending_balance['lendings'] != None):
                lending_dct = lending_balance['lendings']
                for contract, info in lending_dct.items():
                    deposit_info = info['depositChangeLogs']
                    deposit_value = deposit_borrow_info(deposit_info, self.str_timestamp)
                    borrow_info = info['borrowChangeLogs']
                    borrow_value = deposit_borrow_info(borrow_info, self.str_timestamp)

                    rating = deposit_value + borrow_value
                    lending_contract_lst.append(contract)
                    lending_user_lst.append(lending_users['_id'])
                    lending_rating_lst.append(rating)
            else:
                if not os.path.exists(f'data/log_file/lendings'):
                    try:
                        os.makedirs(f'data/log_file/lending')
                    except Exception as ex:
                        with open(f'data/log_file/lending/failed_addresses.json', 'a') as f:
                            f.write(json.dumps(lending_users['_id']))
                            f.write("\n")
                else:
                    with open(f'data/log_file/lending/failed_addresses.json', 'a') as f:
                        f.write(json.dumps(lending_users['_id']))
                        f.write("\n")

        lending_user_rating_dict['contract']  = lending_contract_lst
        lending_user_rating_dict['address'] = lending_user_lst
        lending_user_rating_dict['rating'] = lending_rating_lst
        lending_user_rating_df = pd.DataFrame(lending_user_rating_dict)
        self.lending_address_lst.append(lending_user_rating_df)

    def _get_contract_user_items(self, works):
        for work in works:    
            cursor = self.mongo_clt._db['addresses_searching_18_3'] \
                    .find({},{'_id':1,'interactedWallet':1})
            rows = []
            for cur in cursor[work-self.batch_size: work]:
                for wallet, wallet_data in cur['interactedWallet'].items():
                    if wallet in self.contract_set:
                        for token, contract_data in wallet_data['contractAddress'].items():
                            for i in range(len(contract_data['timestampHistory'])):
                                if i <= self.timestamp:
                                    row = {
                                        'address': cur['_id'],
                                        'contract': wallet,
                                        'tokens': token,
                                        'timestampHistory': contract_data['timestampHistory'][i],
                                        'valueInUSDHistory': contract_data['valueInUSDHistory'][i],
                                        'amountHistory': contract_data['amountHistory'][i]
                                    }
                                    rows.append(row)
            contract_user_rating_df = pd.DataFrame(rows)
            contract_user_rating_df = contract_user_rating_df.groupby(['contract','address']).agg({"valueInUSDHistory":"sum"}).reset_index().rename(columns={"valueInUSDHistory":"rating"})
            self.contract_address_lst.append(contract_user_rating_df)






    def _end(self):
        super()._end() 
        if self.direction=='lendings':
            lending_address_df = pd.concat(self.lending_address_lst)       
            lending_address_df.to_csv(self.saving_path, index=False)
        elif self.direction=='contracts':
            contract_address_df = pd.concat(self.contract_address_lst)
            contract_address_df.to_csv(self.saving_path, index=False)





    