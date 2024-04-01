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
    def __init__(self, mongo_klg, mongo_clt, index_lst, aave_addresses, saving_path, timestamp, max_workers= 4, batch_size=500):
        """
        users - items:
        Aave Contract will be users
        Aave users will be items    
        
        """
        self.mongo_klg = mongo_klg
        self.mongo_clt = mongo_clt

        self.aave_addresses = aave_addresses

        self.batch_size = batch_size
        self.saving_path = saving_path
        self.direction = 'lendings'
        self.timestamp = str(timestamp)

        self.contract_address_lst = []
        super().__init__(work_iterable=index_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        if self.direction =='lendings':
            self._get_aave_user_items(works)

    def _get_aave_user_items(self, works):
        contract_user_rating_dict ={}
        aave_contract_lst =list()
        aave_user_lst = list()
        aave_rating_lst = list()

        for work in works:
            cursor = self.mongo_klg._db['wallets'].find({'_id':{ '$in': self.aave_addresses}},{'_id':1, 'lendings':1})
            balance_lst = ['_id','lendings']
            for aave_users in cursor[work-self.batch_size: work]:
                aave_balance =  {key: aave_users.get(key) for key in balance_lst}
                if (aave_balance['lendings'] != {})&(aave_balance['lendings'] != None):
                    lending_dct = aave_balance['lendings']
                    for contract, info in lending_dct.items():
                        deposit_info = info['depositChangeLogs']
                        deposit_value = deposit_borrow_info(deposit_info, self.timestamp)
                        borrow_info = info['borrowChangeLogs']
                        borrow_value = deposit_borrow_info(borrow_info, self.timestamp)

                        rating = deposit_value + borrow_value
                        aave_contract_lst.append(contract)
                        aave_user_lst.append(aave_users['_id'])
                        aave_rating_lst.append(rating)
                else:
                    if not os.path.exists(f'data/log_file/lendings'):
                        try:
                            os.makedirs(f'data/log_file/lending')
                        except Exception as ex:
                            with open(f'data/log_file/lending/failed_addresses.json', 'a') as f:
                                f.write(json.dumps(aave_users['_id']))
                                f.write("\n")
                    else:
                        with open(f'data/log_file/lending/failed_addresses.json', 'a') as f:
                            f.write(json.dumps(aave_users['_id']))
                            f.write("\n")

        contract_user_rating_dict['contract']  = aave_contract_lst
        contract_user_rating_dict['address'] = aave_user_lst
        contract_user_rating_dict['rating'] = aave_rating_lst


        contract_user_rating_df = pd.DataFrame(contract_user_rating_dict)
        self.contract_address_lst.append(contract_user_rating_df)



    def _get_contract_user_item(self, works):
        for work in works:
            cursor = self.mongo_clt._db['addresses_searching_18_3'].find({'':{ '$in': self.aave_addresses}},{'_id':1, 'lendings':1})
            balance_lst = ['_id','lendings']
            for aave_users in cursor[work-self.batch_size: work]:
                aave_balance =  {key: aave_users.get(key) for key in balance_lst}
                if (aave_balance['lendings'] != {})&(aave_balance['lendings'] != None):
                    lending_dct = aave_balance['lendings']
                    for contract, info in lending_dct.items():
                        deposit_info = info['depositChangeLogs']
                        deposit_value = deposit_borrow_info(deposit_info, self.timestamp)
                        borrow_info = info['borrowChangeLogs']
                        borrow_value = deposit_borrow_info(borrow_info, self.timestamp)

                        rating = deposit_value + borrow_value
                        aave_contract_lst.append(contract)
                        aave_user_lst.append(aave_users['_id'])
                        aave_rating_lst.append(rating)







    def _end(self):
        super()._end() 
        contract_address_df = pd.concat(self.contract_address_lst)       
        contract_address_df.to_csv(self.saving_path, index=False)




    