import json
import numpy as np
import pandas as pd
from utils.list_dict_utils import largest_key_smaller_than, flatten_and_concat, have_common_tags
from constants.dapps_tokens_constans import Dapps
from databases.mongodb_entity import MongoDBEntity


## supporting process
def get_label(row, threshold):
    if row['reputationScore'] >= threshold:
        return 1
    else: 
        return 0

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

def get_tags(tags):
    depositors = []
    borrowers = []
    for tag in tags:
        if tag.split('_')[-1] =='depositors':
            depositors.append(tag)
        if tag.split('_')[-1] =='borrowers':
            borrowers.append(tag)
    lending_tags = [depositors, borrowers]
    return lending_tags


def average_value(dictionary, timestamp):
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
    value_of_largest_key = sum(sub_dict.values())/ len(sub_dict)

    return value_of_largest_key


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
## row process
def get_dapps_balance(dapps_name, dapps_balance, row, timestamp):
    dapps_tokens = Dapps(dapps_name=dapps_name)
    tokens_balance =[]
    if ('tokenChangeLogs' in dapps_balance) :
        if (row['tokenChangeLogs'] == {}):
            tokens_balance.append(0)
        else:
            for token, value_history in row['tokenChangeLogs'].items():
                if token in dapps_tokens.tokens[row['chainId']]:
                        if value_history == {}:
                            value = 0
                        else:
                            largest_key = largest_key_smaller_than(value_history, timestamp,  type='train')
                            if largest_key == 0:
                                value = 0
                            else:
                                last_value = value_history[largest_key]
                                value = last_value['valueInUSD']
                        tokens_balance.append(value)
                else: 
                    tokens_balance.append(0)        
    elif 'tokens' in dapps_balance:
        chain_id = row['chainId']
        for token, value_history in row['tokens'].items():
            if token in dapps_tokens.tokens[row['chainId']]:
                tokens = list(MongoDBEntity()._db['smart_contracts'].find({'_id':f'{chain_id}_{token}'}, {'priceChangeLogs':1, 'price':1}))[0]
                if 'priceChangeLogs' in tokens:
                    largest_key = largest_key_smaller_than(tokens['priceChangeLogs'], timestamp, type='train')
                    if largest_key == 0:
                        value = 0
                    else:
                        value = value_history*(tokens['priceChangeLogs'][largest_key])
                elif 'price' in tokens:
                    value = value_history*(tokens['price'])
                else:
                    value = 0
                tokens_balance.append(value)
            else:
                tokens_balance.append(0)
    else:
        tokens_balance.append(0)
    return np.sum(tokens_balance)
        
def get_balance(row, timestamp, type='search'):
    if 'balanceChangeLogs' in row:
        if row['balanceChangeLogs'] != 0:
            if row['balanceChangeLogs'] =={}:
                return row['balanceInUSD']
            else:
                largest_key = largest_key_smaller_than(row['balanceChangeLogs'], timestamp, type=type)
                if largest_key == 0:
                    last_value = row['balanceInUSD']
                else:
                    last_value = row['balanceChangeLogs'][str(largest_key)]
                return last_value
                
    return row['balanceInUSD']

def get_deposit_features(row, timestamp, dapps_balance, lending_tags, dapps_tags):
    if have_common_tags(lending_tags[0], dapps_tags):
        if ('depositChangeLogs' in dapps_balance):
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
        
    else:
        return 'outdated'

def get_borrow_features(row, timestamp, dapps_balance, lending_tags, dapps_tags):
    if have_common_tags(lending_tags[1], dapps_tags):
        if ('borrowChangeLogs' in dapps_balance):
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
        
    else:
        return 'outdated'

def get_reputation_score(row):
    if row['dappsBalance']==0:        
        if (row['dappsAvgDeposit']=='outdated')&(row['dappsAvgBorrow']=='outdated'):
            return 0 ## outdated data

        elif (((row['dappsAvgDeposit'] in ['future data','outdated'])&(row['dappsAvgBorrow']=='future data'))|((row['dappsAvgBorrow'] in ['future data','outdated'])&(row['dappsAvgDeposit']=='future data'))):
            return -1 ## future data
        else:
            row = row.replace('future data', 0)
            row = row.replace('outdated', 0)
            return (row['dappsBalance'] + row['dappsAvgDeposit']+ row['dappsAvgBorrow'])/3

    else:
        row = row.replace('future data', 0)
        row = row.replace('outdated', 0)
        return (row['dappsBalance'] + row['dappsAvgDeposit']+ row['dappsAvgBorrow'])/3

##  df process

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
    Dapps_token_transfer = Dapps_transaction_clean.groupby(['_id','tokens']) \
                                    .agg({"valueInUSDHistory":tuple}).reset_index()
    Dapps_token_transfer['totalInUSD'] = Dapps_token_transfer['valueInUSDHistory'].apply(sum)
    Dapps_tokens = Dapps_token_transfer.pivot_table(values=['totalInUSD'], index='_id', \
                                    columns='tokens', aggfunc='sum', fill_value = 0) \
                                    .reset_index()
    column_lst = ['_id']
    column_lst.extend(['{}'.format(col[1]) for col in Dapps_tokens.columns if col[0]!='_id'])
    Dapps_tokens.columns = column_lst
    Dapps_value_transfer = Dapps_transaction_clean.groupby(['_id']) \
                                    .agg({"valueInUSDHistory":tuple}).reset_index()
    Dapps_value_transfer['totalUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(sum)
    Dapps_value_transfer['avgUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(np.median)
    Dapps_value = Dapps_value_transfer[['_id','totalUSDTransfer','avgUSDTransfer']] \
                                    .merge(Dapps_tokens, on ='_id',how='inner')

    return Dapps_value

def get_only_value_features(Dapps_transaction_clean):
    Dapps_value_transfer = Dapps_transaction_clean.groupby(['_id']) \
                                    .agg({"valueInUSDHistory":tuple}).reset_index()
    Dapps_value_transfer['totalUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(sum)
    Dapps_value_transfer['avgUSDTransfer'] = Dapps_value_transfer['valueInUSDHistory'].apply(np.median)
    Dapps_value = Dapps_value_transfer[['_id','totalUSDTransfer','avgUSDTransfer']]
    return Dapps_value

def map_contracts(row, token_lst):
    token= row['chainId']+'_'+row['contractAddress']
    if token in token_lst[0]: #[native_tokens, stable_tokens, top_tokens, other_tokens]
        return 'nativeTokens'
    elif token in token_lst[1]:
        return 'stableTokens'
    elif token in token_lst[2]:
        return 'topTokens'
    else:
        return 'otherTokens'
    

def get_df_v2(data, token_lst):
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
    df['chainId'] = df['_id'].apply(lambda x: x.split('_')[0])
    df['tokens'] =  df.apply(lambda row: map_contracts(row, token_lst), axis=1)

    return df[['_id', 'interactedWallet', 'tokens', 'contractAddress','timestampHistory', 'valueInUSDHistory', 'amountHistory']]

def get_balance_features(dapps_name, lending_tags, dapps_balance, timestamp):
    #tags 

    dapps_tags = dapps_balance['tags']
    #balance
    profile_elite = pd.DataFrame([dapps_balance])
    profile_elite['dappsBalance'] = profile_elite.apply(
        lambda row: get_dapps_balance(dapps_name=dapps_name,
                                      dapps_balance=dapps_balance, 
                                      #chain_id=chain_id, 
                                      row=row, 
                                      timestamp=timestamp), axis=1)    
    
    # profile_elite['overallBalance'] = profile_elite.apply(
    #     lambda row: get_balance(row=row, 
    #                             timestamp=timestamp, type='train'), axis=1)

    #if have_common_tags(lending_tags[0], dapps_tags):
    profile_elite['dappsAvgDeposit'] = profile_elite.apply(
        lambda row: get_deposit_features(row=row, 
                                        timestamp=timestamp,
                                        lending_tags=lending_tags, 
                                        dapps_tags=dapps_tags,
                                        dapps_balance=dapps_balance), axis=1
        )

    
    profile_elite['dappsAvgBorrow'] = profile_elite.apply(
        lambda row: get_borrow_features(row=row, 
                                         timestamp=timestamp,
                                         lending_tags=lending_tags,
                                         dapps_tags=dapps_tags,
                                         dapps_balance=dapps_balance), axis=1
        )

    profile_elite['reputationScore'] = profile_elite.apply(
        lambda row: get_reputation_score(row=row), axis=1
    )
    



    # if profile_elite['dappsBalance'].iloc[0] ==0:
        
    #     if (profile_elite['dappsAvgDeposit'].iloc[0]=='outdated')&(profile_elite['dappsAvgBorrow'].iloc[0]=='outdated'):
    #         profile_elite['reputationScore'] = 0
    #         return  profile_elite[['_id','overallBalance','reputationScore']], 'outdated'
    #     elif (((profile_elite['dappsAvgDeposit'].iloc[0] in ['future data','outdated'])&(profile_elite['dappsAvgBorrow'].iloc[0]=='future data'))|((profile_elite['dappsAvgBorrow'].iloc[0] in ['future data','outdated'])&(profile_elite['dappsAvgDeposit'].iloc[0]=='future data'))):
    #         return pd.DataFrame(), 'future data'
    #     else:
    #         profile_elite = profile_elite.replace('future data', 0)
    #         profile_elite = profile_elite.replace('outdated', 0)
    #         profile_elite['reputationScore'] = (profile_elite['dappsBalance'] + profile_elite['dappsAvgDeposit']+ profile_elite['dappsAvgBorrow'])/3

    # else:
    #     profile_elite = profile_elite.replace('future data', 0)
    #     profile_elite = profile_elite.replace('outdated', 0)
    #     profile_elite['reputationScore'] = (profile_elite['dappsBalance'] + profile_elite['dappsAvgDeposit']+ profile_elite['dappsAvgBorrow'])/3

    Dapps_balance = profile_elite[['_id', 'dappsAvgDeposit', 'dappsAvgBorrow', 'dappsBalance', 'reputationScore']]

    return Dapps_balance

def search_balance_feature(dapps_balance, timestamp):
    if 'balanceChangeLogs' not in dapps_balance.columns:
        dapps_balance['balanceChangeLogs'] = 0

    if 'balanceInUSD' not in dapps_balance.columns:
        dapps_balance['balanceInUSD'] = 0
    dapps_balance['overallBalance'] = dapps_balance.apply(lambda row: get_balance(row,timestamp), axis=1)
    Dapps_balance = dapps_balance[['_id','overallBalance']]
    return Dapps_balance

