import json
import numpy as np
import pandas as pd
from utils.list_dict_utils import largest_key_smaller_than, flatten_and_concat
from constants.dapps_tokens_constans import Dapps

def get_label(row, threshold):
    if row['reputationScore'] >= threshold:
        return 1
    else: 
        return 0


# def get_token_balance(row, timestamp):
#     tokens_balance =[]
#     if (row == 0) |(row == {}):
#         tokens_balance.append(0)
#     else:
#         for token, value_history in row.items():
#             if value_history == {}:
#                 value = 0
#             else:
#                 largest_key = largest_key_smaller_than(value_history, timestamp)
#                 if largest_key ==0:
#                     value = 0
#                 else:
#                     last_value = value_history[largest_key]
#                     value = last_value['valueInUSD']
#             tokens_balance.append(value)

#     return tokens_balance
        

def get_dapps_balance(dapps_name, dapps_balance, row, timestamp):
#    previous_2month = str(int(timestamp) - 2678400*2)
    dapps_tokens = Dapps(dapps_name=dapps_name)
    tokens_balance =[]
    if ('tokenChangeLogs' in dapps_balance) | (row['tokenChangeLogs']!=0) :
        if (row['tokenChangeLogs'] == {}):
            tokens_balance.append(0)
        else:
            for token, value_history in row['tokenChangeLogs'].items():
                if token in dapps_tokens.tokens[row['chainId']]:
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
    elif 'tokens' in dapps_balance:
        for token, value_history in row['tokens'].items():
            tokens_balance.append(value_history)
    else:
        tokens_balance.append(0)

                

    return np.sum(tokens_balance)
    
    
        
def get_balance(row, timestamp):
    if row['balanceChangeLogs'] != 0:
        if row['balanceChangeLogs'] =={}:
            return 0
        else:
            
            largest_key = largest_key_smaller_than(row['balanceChangeLogs'], timestamp)
            if largest_key == 0:
                last_value = 0
            else:
                last_value = row['balanceChangeLogs'][str(largest_key)]
            return last_value
    else:
        return row['balanceInUSD']

def average_value(dictionary, timestamp):
  #  previous3month = str(int(timestamp) - 2678400*3)
    if (dictionary =={}) |(dictionary ==0):
        return 'outdated'
    elif not dictionary:
        return 'outdated'
    
    sub_dict = {key: value for key, value in dictionary.items() if (key <= timestamp)}  
    if sub_dict =={}:
        future_subdict = {key: value for key, value in dictionary.items() if key > timestamp}
        if (future_subdict =={}):
            return 'outdated'
        else:
            value = np.sum(list(future_subdict.values()))
            if value ==0:
                return 'outdated'
            else: 
                return 'future data'


    #largest_key = max(sub_dict.keys())
    #value_of_largest_key = sub_dict[largest_key] ## Get the latest value

    value_of_largest_key = sum(sub_dict.values())/ len(sub_dict)


    return value_of_largest_key

def get_deposit_features(row, timestamp, dapps_balance):
    if ('depositChangeLogs' in dapps_balance) &(row['depositChangeLogs'] != 0):
        avg_value = average_value(dictionary=row['depositChangeLogs'],
                      timestamp=timestamp)
        return avg_value
    elif 'depositInUSD' in dapps_balance:
        if dapps_balance['depositInUSD'] == 0:
            return 'outdated'
        else:
            return dapps_balance['depositInUSD']
    else:
        return 'outdated'

def get_borrow_features(row, timestamp, dapps_balance):
    if ('borrowChangeLogs' in dapps_balance) & (row['borrowChangeLogs'] !=0):
        avg_value = average_value(dictionary=row['borrowChangeLogs'],
                      timestamp=timestamp)
        return avg_value
    elif 'borrowInUSD' in dapps_balance:
        if dapps_balance['borrowInUSD'] == 0:
            return 'outdated'
        else:
            return dapps_balance['borrowInUSD']
    
    else:
        return 'outdated'


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

def get_value_features(Dapps_transaction_clean, chain_id, mongo_klg):
    #valueInUSD
    Dapps_token_transfer = Dapps_transaction_clean.groupby(['_id','contractAddress']) \
                                    .agg({"valueInUSDHistory":tuple}).reset_index()
    Dapps_token_transfer['totalInUSD'] = Dapps_token_transfer['valueInUSDHistory'].apply(sum)
    Dapps_tokens = Dapps_token_transfer.pivot_table(values=['totalInUSD'], index='_id', \
                                    columns='contractAddress', aggfunc='sum', fill_value = 0) \
                                    .reset_index()
    column_lst = []
    column_lst.extend(['{}_{}'.format(chain_id, col[1]) for col in Dapps_tokens.columns if col[0]!='_id'])
    new_column_lst = ['_id']
    for col in column_lst:
        cursor = mongo_klg._db['smart_contracts'].find({"_id":col},{"_id":1,"idCoingecko":1})
        token_id = 'value-'+list(cursor)[0]['idCoingecko']
        new_column_lst.append(token_id)

    Dapps_tokens.columns = new_column_lst
    Dapps_value_transfer = Dapps_transaction_clean.groupby(['_id']) \
                                    .agg({"valueInUSDHistory":tuple}).reset_index()
    Dapps_value_transfer['totalUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(sum)
    Dapps_value_transfer['avgUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(np.median)
    Dapps_value = Dapps_value_transfer[['_id','totalUSDTransfer','avgUSDTransfer']] \
                                    .merge(Dapps_tokens, on ='_id',how='inner')
    new_column_lst.remove('_id')
    return Dapps_value, new_column_lst

def get_only_value_features(Dapps_transaction_clean):
    #valueInUSD
    #Dapps_token_transfer = Dapps_transaction_clean.groupby(['_id','contractAddress']) \
    #                                .agg({"valueInUSDHistory":tuple}).reset_index()
    #Dapps_token_transfer['totalInUSD'] = Dapps_token_transfer['valueInUSDHistory'].apply(sum)
    # Dapps_tokens = Dapps_token_transfer.pivot_table(values=['totalInUSD'], index='_id', \
    #                                 columns='contractAddress', aggfunc='sum', fill_value = 0) \
    #                                 .reset_index()
    # column_lst = []
    # column_lst.extend(['{}_{}'.format(chain_id, col[1]) for col in Dapps_tokens.columns if col[0]!='_id'])
    # new_column_lst = ['_id']
    # for col in column_lst:
    #     cursor = mongo_klg._db['smart_contracts'].find({"_id":col},{"_id":1,"idCoingecko":1})
    #     token_id = 'value-'+list(cursor)[0]['idCoingecko']
    #     new_column_lst.append(token_id)

    # Dapps_tokens.columns = new_column_lst
    Dapps_value_transfer = Dapps_transaction_clean.groupby(['_id']) \
                                    .agg({"valueInUSDHistory":tuple}).reset_index()
    Dapps_value_transfer['totalUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(sum)
    Dapps_value_transfer['avgUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(np.median)
    Dapps_value = Dapps_value_transfer[['_id','totalUSDTransfer','avgUSDTransfer']]
    #new_column_lst.remove('_id')
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

def get_df_v2(data):
    rows = []
    for wallet, wallet_data in data['interactedWallet'].items():
        for contract, contract_data in wallet_data['contractAddress'].items():
            for timestamp, values in contract_data.items():
                row = {
                    '_id': data['_id'],
                    'interactedWallet': wallet,
                    'contractAddress': contract,
                    'timestampHistory': timestamp,
                    'valueInUSDHistory': values['value'],
                    'amountHistory': values['amount']
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    return df

def get_balance_features(dapps_name, chain_id, dapps_balance, timestamp):
    #balance
    profile_elite = pd.DataFrame([dapps_balance])
    profile_elite['dappsBalance'] = profile_elite.apply(
        lambda row: get_dapps_balance(dapps_name=dapps_name,
                                      dapps_balance=dapps_balance, 
                                      chain_id=chain_id, 
                                      row=row, 
                                      timestamp=timestamp), axis=1)    
    
    profile_elite['overallBalance'] = profile_elite.apply(
        lambda row: get_balance(row=row, 
                                timestamp=timestamp), axis=1)

    profile_elite['aaveAvgDeposit'] = profile_elite.apply(
        lambda row: get_deposit_features(row=row, 
                                         timestamp=timestamp,
                                         dapps_balance=dapps_balance), axis=1
        )
    
    profile_elite['aaveAvgBorrow'] = profile_elite.apply(
        lambda row: get_borrow_features(row=row, 
                                         timestamp=timestamp,
                                         dapps_balance=dapps_balance), axis=1
        )
    
    #profile_elite['aaveAvgBorrow'] = profile_elite['borrowChangeLogs'].apply(lambda row: average_value(row, timestamp))
    if profile_elite['dappsBalance'].iloc[0] ==0:
        
        if (profile_elite['aaveAvgDeposit'].iloc[0]=='outdated')&(profile_elite['aaveAvgBorrow'].iloc[0]=='outdated'):
            return pd.DataFrame(), 'outdated'
        elif (((profile_elite['aaveAvgDeposit'].iloc[0] in ['future data','outdated'])&(profile_elite['aaveAvgBorrow'].iloc[0]=='future data'))|((profile_elite['aaveAvgBorrow'].iloc[0] in ['future data','outdated'])&(profile_elite['aaveAvgDeposit'].iloc[0]=='future data'))):
            return pd.DataFrame(), 'future data'
        else:
            profile_elite = profile_elite.replace('future data', 0)
            profile_elite = profile_elite.replace('outdated', 0)
            profile_elite['reputationScore'] = (profile_elite['dappsBalance'] + profile_elite['aaveAvgDeposit']+ profile_elite['aaveAvgBorrow'])/3



    else:
        profile_elite = profile_elite.replace('future data', 0)
        profile_elite = profile_elite.replace('outdated', 0)
        profile_elite['reputationScore'] = (profile_elite['dappsBalance'] + profile_elite['aaveAvgDeposit']+ profile_elite['aaveAvgBorrow'])/3

    Dapps_balance = profile_elite[['_id','overallBalance','reputationScore']]

    return Dapps_balance, 'acceptable'

def search_balance_feature(dapps_balance, timestamp):
    if 'balanceChangeLogs' not in dapps_balance.columns:
        dapps_balance['balanceChangeLogs'] = 0

    if 'balanceInUSD' not in dapps_balance.columns:
        dapps_balance['balanceInUSD'] = 0
    dapps_balance['overallBalance'] = dapps_balance.apply(lambda row: get_balance(row,timestamp), axis=1)
    Dapps_balance = dapps_balance[['_id','overallBalance']]
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

