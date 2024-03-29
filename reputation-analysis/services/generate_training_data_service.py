import bisect
import json
import os
import pandas as pd 
import numpy as np
from multithread_processing.base_job import BaseJob
from utils.logger_utils import get_logger

def flatten_and_concat(tuples):
    flattened = [item for sublist in tuples for item in sublist]
    return tuple(flattened)

def calculate_impurity_numeric(data):
    std_deviation = np.std(data)
    return std_deviation

def largest_key_smaller_than(dictionary, value):
    keys = sorted(dictionary.keys())
    index = bisect.bisect_left(keys, value) - 1
    if index >= 0:
        return keys[index]
    else:
        return 0


def remove_outliers_iqr(df, columns):
    cleaned_df = df.copy()
    for col in columns:

        Q1 = df[col].quantile(0.15)
        Q3 = df[col].quantile(0.85)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        cleaned_df = cleaned_df[(cleaned_df[col] >= lower_bound) & (cleaned_df[col] <= upper_bound)]
    
    return cleaned_df

def get_label(row, threshold):
    if row['reputationScore'] >= threshold:
        return 1
    else: 
        return 0


def get_token_balance(row, timestamp):
    tokens_balance =[]
    if (row == 0) |(row == {}):
        tokens_balance.append(0)
    else:
        for token, value_history in row.items():
            if value_history == {}:
                value = 0
            else:
                largest_key = largest_key_smaller_than(value_history, timestamp)
                if largest_key ==0:
                    value = 0
                else:
                    last_value = value_history[largest_key]
                    value = last_value['valueInUSD']
            tokens_balance.append(value)

    return tokens_balance
        

def get_aave_balance(row, timestamp):
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
    
    
    
def get_inactive_user(row):
    if row['balance'] <= 100:
        return 'inactive'
    else:
        return row['score_label']


def average_value(dictionary, timestamp):
    previous_1month = timestamp - 2678400 
    if dictionary =={}:
        return 0
    elif dictionary == 0:
        return 0 
    elif not dictionary:
        return None
    
    sub_dict = {key: value for key, value in dictionary.items() if key > previous_1month}  
    if sub_dict =={}:
        return 0
    if sub_dict ==0:
        return 0
    return np.mean(list(sub_dict.values()))

def get_freq_features(Dapps_transaction_clean):
    #frequency
    Dapps_transaction_clean_info = Dapps_transaction_clean.groupby(['_id','interactedWallet','contractAddress']) \
                                    .agg({'timestampHistory':tuple}).reset_index()
    Dapps_transaction_clean_info['tokenInteractTimes'] =Dapps_transaction_clean_info['timestampHistory'].apply(len)
    Dapps_transaction_clean_info['addressInteractTime'] = Dapps_transaction_clean_info['timestampHistory'].apply(len)
    Dapps_transaction_clean_info_token = Dapps_transaction_clean_info.groupby(['_id','contractAddress']) \
                                    .agg({'tokenInteractTimes':'sum'}).reset_index()
    Dapps_transaction_clean_info_tokens = Dapps_transaction_clean_info_token.groupby('_id') \
                                    .agg({'contractAddress':'count', 'tokenInteractTimes': tuple}).reset_index()
    Dapps_transaction_clean_info_address = Dapps_transaction_clean_info.groupby(['_id','interactedWallet']) \
                                    .agg({'addressInteractTime':'sum'}).reset_index()
    Dapps_transaction_clean_info_addresses = Dapps_transaction_clean_info_address.groupby('_id') \
                                    .agg({'interactedWallet':'count', 'addressInteractTime': tuple}).reset_index()
    Dapps_freq_info = Dapps_transaction_clean_info.groupby('_id') \
                                    .agg({'timestampHistory':flatten_and_concat}).reset_index()
    
    Dapps_freq_info = Dapps_freq_info.merge(Dapps_transaction_clean_info_tokens, how='inner', on='_id')
    Dapps_freq_info = Dapps_freq_info.merge(Dapps_transaction_clean_info_addresses, how='inner', on='_id')
    Dapps_freq_info['noTransaction'] = Dapps_freq_info['timestampHistory'].apply(len)
    Dapps_freq_info['addressTimeStd'] = Dapps_freq_info['addressInteractTime'].apply(lambda row: np.std(row))
    Dapps_freq_info['tokenTimeStd'] = Dapps_freq_info['tokenInteractTimes'].apply(lambda row: np.std(row))
    Dapps_freq_info.rename(columns = {"contractAddress":"numInteractedToken","interactedWallet":"numInteractedWallet"}, inplace = True)
    Dapps_freq = Dapps_freq_info[['_id','numInteractedToken','numInteractedWallet','addressTimeStd','tokenTimeStd','noTransaction']]
    return Dapps_freq

def get_value_features(Dapps_transaction_clean):
    #valueInUSD
    Dapps_token_transfer = Dapps_transaction_clean.groupby(['_id','contractAddress']) \
                                    .agg({"valueInUSDHistory":tuple}).reset_index()
    Dapps_token_transfer['totalInUSD'] = Dapps_token_transfer['valueInUSDHistory'].apply(sum)
    Dapps_tokens = Dapps_token_transfer.pivot_table(values=['totalInUSD'], index='_id', \
                                    columns='contractAddress', aggfunc='sum', fill_value = 0) \
                                    .reset_index()
    column_lst = ['_id']
    column_lst.extend(['{}_{}'.format(col[0], col[1]) for col in Dapps_tokens.columns if col[0]!='_id'])
    Dapps_tokens.columns = column_lst
    Dapps_value_transfer = Dapps_transaction_clean.groupby(['_id']) \
                                    .agg({"valueInUSDHistory":tuple}).reset_index()
    Dapps_value_transfer['totalUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(sum)
    Dapps_value_transfer['avgUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(np.median)
    Dapps_value = Dapps_value_transfer[['_id','totalUSDTransfer','avgUSDTransfer']] \
                                    .merge(Dapps_tokens, on ='_id',how='inner')
    return Dapps_value

def get_df(data):
    rows = []
    for wallet, wallet_data in data['interactedWallet'].items():
        for contract, contract_data in wallet_data['contractAddress'].items():
            for i in range(len(contract_data['timestampHistory'])):
                row = {
                    '_id': data['_id'],
                    'interactedWallet': wallet,
                    'contractAddress': contract,
                    'timestampHistory': contract_data['timestampHistory'][i],
                    'valueInUSDHistory': contract_data['valueInUSDHistory'][i],
                    'amountHistory': contract_data['amountHistory'][i]
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    return df

def get_balance_features(profile_elite, timestamp):
    #balance

    #profile_elite['tokenChangeLogs'].fillna("0", inplace=True)
    #profile_elite['tokenBalances'] = profile_elite['tokenChangeLogs'].apply(lambda row: get_token_balance(row,timestamp))
    profile_elite['aaveBalance'] = profile_elite['tokenChangeLogs'].apply(lambda row: get_aave_balance(row, timestamp))
    profile_elite['overallBalance'] = profile_elite['balanceChangeLogs'].apply(lambda row: get_balance(row, timestamp))
    profile_elite['aaveAvgDeposit'] = profile_elite['depositChangeLogs'].apply(lambda row: average_value(row, timestamp))
    profile_elite['aaveAvgBorrow'] = profile_elite['borrowChangeLogs'].apply(lambda row: average_value(row, timestamp))
    profile_elite['reputationScore'] = (profile_elite['aaveBalance'] + profile_elite['aaveAvgDeposit']+ profile_elite['aaveAvgBorrow'])/3
#    profile_elite['tokenBalanceStd'] = profile_elite['tokenBalances'].apply(np.std)
    Dapps_balance = profile_elite[['_id','overallBalance','reputationScore']]
    return Dapps_balance
def search_balance_feature(profile_elite, timestamp):
    # profile_elite['tokenChangeLogs'].fillna("0", inplace=True)
    # profile_elite['tokenBalances'] = profile_elite['tokenChangeLogs'].apply(lambda row: get_token_balance(row, timestamp))
    profile_elite['overallBalance'] = profile_elite['balanceChangeLogs'].apply(lambda row: get_balance(row, timestamp))

#    profile_elite['tokenBalanceStd'] = profile_elite['tokenBalances'].apply(np.std)
    Dapps_balance = profile_elite[['_id','overallBalance']]
    return Dapps_balance

def update_json_file(address, removed_path):
    with open(removed_path, 'r+') as file:
        try:
            existing_data = json.load(file)
        except json.JSONDecodeError:
            print('start to append')
            existing_data = []
        for data in address:
            existing_data.append(data)
        
        file.seek(0)
        json.dump(existing_data, file, indent=4)

def write_to_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

class GenerateData(BaseJob):
    def __init__(self, direction, importer, exporter, name, index_lst, aave_addresses, timestamp, max_workers= 4, batch_size=500):
        self.importer = importer
        self.exporter = exporter
        self.name = name
        self.batch_size = batch_size
        self.aave_address = aave_addresses
        self.direction = direction
        self.timestamp = timestamp
        self.timestamp_str = str(timestamp)
        super().__init__(work_iterable=index_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        if self.direction =='train':
            for work in works:
                cursor = self.importer.find({'_id':{ '$in': self.aave_address}},{'_id':1,'interactedWallet':1,'tokenChangeLogs':1,'balanceChangeLogs':1,'depositChangeLogs':1,'borrowChangeLogs':1})
                transact_lst = ['_id','interactedWallet']
                balance_lst = ['_id','balanceChangeLogs','depositChangeLogs','borrowChangeLogs','tokenChangeLogs']
                info_df_lst = []
                for aave_users in cursor[work-self.batch_size: work]:
                    try:
                        aave_transac = {key: aave_users.get(key) for key in transact_lst}
                        aave_balance =  {key: aave_users.get(key) for key in balance_lst}
                        transac_df = get_df(aave_transac)
                        transac_df = transac_df[transac_df['timestampHistory']<self.timestamp]
                        value_df = get_value_features(transac_df)
                        freq_df = get_freq_features(transac_df)
                        balance_df = get_balance_features(pd.DataFrame([aave_balance]), self.timestamp_str)
                        info_df = value_df.merge(freq_df, on='_id',how = 'inner')
                        info_df = info_df.merge(balance_df, on='_id', how='inner')
                        if info_df.empty:
                            if not os.path.exists(f'data/log_file/{self.name}/train'):
                                os.makedirs(f'data/log_file/{self.name}/train')
                            with open(f'data/log_file/{self.name}/train/failed_addresses.json', 'a') as f:
                                f.write(json.dumps(aave_users['_id']))
                                f.write("\n")
                        else:
                            info_dict = info_df.to_dict(orient='records')
                            info_df_lst.extend(info_dict)
                    except Exception as e:
                        print(e)
                        continue
                if info_df_lst != []:
                    self.exporter.update_data(name=self.name, data=info_df_lst)

        if self.direction =='search':
            for work in works:
                cursor = self.importer.find({},{'_id':1,'interactedWallet':1,'tokenChangeLogs':1,'balanceChangeLogs':1,'depositChangeLogs':1,'borrowChangeLogs':1})
                transact_lst = ['_id','interactedWallet']
                balance_lst = ['_id','balanceChangeLogs','depositChangeLogs','borrowChangeLogs','tokenChangeLogs']
                info_df_lst = []
                try:
                    for aave_users in cursor[work-self.batch_size: work]:
                        try:
                            aave_transac = {key: aave_users.get(key) for key in transact_lst}
                            aave_balance =  {key: aave_users.get(key) for key in balance_lst}
                            transac_df = get_df(aave_transac)

                            transac_df = transac_df[transac_df['timestampHistory']<self.timestamp]
                            value_df = get_value_features(transac_df)
                            freq_df = get_freq_features(transac_df)
                            balance_df = search_balance_feature(pd.DataFrame([aave_balance]), self.timestamp_str)
                            info_df = value_df.merge(freq_df, on='_id',how = 'inner')
                            info_df = info_df.merge(balance_df, on='_id', how='inner')
                            if info_df.empty:
                                if not os.path.exists(f'data/log_file/{self.name}/search'):
                                    os.makedirs(f'data/log_file/{self.name}/search')
                                with open(f'data/log_file/{self.name}/search/failed_addresses.json', 'a') as f:
                                    f.write(json.dumps(aave_users['_id']))
                                    f.write("\n")
                            else:
                                info_dict = info_df.to_dict(orient='records')
                                info_df_lst.extend(info_dict)
                        except Exception as e:
                            print(e)
                            continue
                except Exception as ex:
                    print(ex)
                    if info_df_lst != []:
                        self.exporter.update_data(name=self.name, data=info_df_lst)
                    continue
                if info_df_lst != []:
                    self.exporter.update_data(name=self.name, data=info_df_lst)

    def _end(self):
        super()._end()



