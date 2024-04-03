import bisect
import json
import os
import pandas as pd
import numpy as np
from multithread_processing.base_job import BaseJob
from utils.ethereum_utils import filter_out_contracts


def largest_key_smaller_than(dictionary, value):
    keys = sorted(dictionary.keys())
    index = bisect.bisect_left(keys, value) - 1
    if index >= 0:
        return keys[index]
    else:
        return 0
def get_aave_balance(row, timestamp):
    previous_2month = str(int(timestamp) - 2678400*2)
    tokens_balance =[]
    if (row == 0) |(row == {}):
        tokens_balance.append(0)
    else:
        for token, value_history in row.items():
            if (token =='0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9') |(token =='0x4da27a545c0c5b758a6ba100e3a049001de870f5'):       
                if value_history == {}:
                    value = 0
                else:
                    largest_key = largest_key_smaller_than(value_history, timestamp)
                    if largest_key ==0:
                        value = 0
                    elif largest_key <=previous_2month:
                        value = 0
                    else:
                        last_value = value_history[largest_key]
                        value = last_value['valueInUSD']
                tokens_balance.append(value)
            
            else: 
                tokens_balance.append(0)
    return np.sum(tokens_balance)
    
    
        
def get_balance(my_dict, timestamp):
    if my_dict =={}:
        return 0
    else:
        largest_key = largest_key_smaller_than(my_dict, timestamp)
        if largest_key == 0:
            last_value = 0
        else:
            last_value = my_dict[largest_key]
        return last_value
    
def average_value(dictionary, timestamp):
    previous_2month = str(int(timestamp) - 2678400*2)
    if (dictionary =={}) |(dictionary ==0):
        return 0
    elif not dictionary:
        return 0
    
    sub_dict = {key: value for key, value in dictionary.items() if ((key >= previous_2month) &(key <= timestamp))}  
    if sub_dict =={}:
        return 0
    return np.mean(list(sub_dict.values()))

class GetReputationScore(BaseJob):
    def __init__(self, importer, saving_path, aave_address, lst_addresses, timestamp, max_workers= 4, batch_size=500):
        self.importer = importer
        self.saving_path = saving_path
        self.aave_address = aave_address
        self.batch_size = batch_size
        self.timestamp = str(timestamp)

        self.aave_users_list = list()
        super().__init__(work_iterable=lst_addresses,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        for work in works:
            cursor = self.importer.find({'_id':{ '$in': self.aave_address}},{'_id':1,'tokenChangeLogs':1,'balanceChangeLogs':1,'depositChangeLogs':1,'borrowChangeLogs':1})
            balance_lst = ['_id','balanceChangeLogs','depositChangeLogs','borrowChangeLogs','tokenChangeLogs']

            for aave_users in cursor[work-self.batch_size: work]:
                aave_balance =  {key: aave_users.get(key) for key in balance_lst}
                profile_elite = pd.DataFrame([aave_balance])
                profile_elite['aaveBalance'] = profile_elite['tokenChangeLogs'].apply(lambda row: get_aave_balance(row, self.timestamp))
                profile_elite['aaveAvgDeposit'] = profile_elite['depositChangeLogs'].apply(lambda row: average_value(row, self.timestamp))
                profile_elite['aaveAvgBorrow'] = profile_elite['borrowChangeLogs'].apply(lambda row: average_value(row, self.timestamp))
                profile_elite['reputationScore'] = (profile_elite['aaveBalance'] + profile_elite['aaveAvgDeposit']+ profile_elite['aaveAvgBorrow'])/3
                self.aave_users_list.append(profile_elite[['_id','aaveBalance','aaveAvgDeposit','aaveAvgBorrow','reputationScore']])

    def _end(self):
        super()._end() 
        aave_users_df = pd.concat(self.aave_users_list)       
        aave_users_df.to_csv(self.saving_path, index=False)