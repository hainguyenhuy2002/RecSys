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


def get_token_balance(row):
    tokens_balance =[]
    if (row == 0) |(row == {}):
        tokens_balance.append(0)
    else:
        for token, value_history in row.items():
            try:
                if value_history == {}:
                    value = 0
                else:
                    last_key = list(value_history.keys())[-1]
                    last_value = value_history[last_key]
                    value = last_value['valueInUSD']
                tokens_balance.append(value)
            except Exception as e:
                print(value_history)
    return tokens_balance
        

def get_aave_balance(row):
    tokens_balance =[]
    if (row == 0) |(row == {}):
        tokens_balance.append(0)
    else:
        for token, value_history in row.items():
            if (token =='0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9') |(token =='0x4da27a545c0c5b758a6ba100e3a049001de870f5'):       
                try:
                    if value_history == {}:
                        value = 0
                    else:
                        last_key = list(value_history.keys())[-1]
                        last_value = value_history[last_key]
                        value = last_value['valueInUSD']
                    tokens_balance.append(value)
                except Exception as e:
                    print(value_history)
            
            else: 
                tokens_balance.append(0)
    return np.sum(tokens_balance)
    
    
        
def get_balance(my_dict):
    if my_dict =={}:
        return 0
    else:
        last_key = list(my_dict.keys())[-1]
        last_value = my_dict[last_key]
        return last_value
    
    
    
def get_inactive_user(row):
    if row['balance'] <= 100:
        return 'inactive'
    else:
        return row['score_label']


def average_value(dictionary):
    if dictionary =={}:
        return 0
    elif dictionary == 0:
        return 0 
    elif not dictionary:
        return None

    return np.mean(list(dictionary.values()))

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

def get_balance_features(profile_elite):
    #balance

    profile_elite['tokenChangeLogs'].fillna("0", inplace=True)
    profile_elite['tokenBalances'] = profile_elite['tokenChangeLogs'].apply(get_token_balance)
    profile_elite['aaveBalance'] = profile_elite['tokenChangeLogs'].apply(get_aave_balance)
    profile_elite['overallBalance'] = profile_elite['balanceChangeLogs'].apply(get_balance)
    profile_elite['aaveAvgDeposit'] = profile_elite['depositChangeLogs'].apply(average_value)
    profile_elite['aaveAvgBorrow'] = profile_elite['borrowChangeLogs'].apply(average_value)
    profile_elite['reputationScore'] = (profile_elite['aaveBalance'] + profile_elite['aaveAvgDeposit']+ profile_elite['aaveAvgBorrow'])/3
    profile_elite['tokenBalanceStd'] = profile_elite['tokenBalances'].apply(np.std)
    Dapps_balance = profile_elite[['_id','tokenBalanceStd','overallBalance','reputationScore']]
    return Dapps_balance
def search_balance_feature(profile_elite):
    profile_elite['tokenChangeLogs'].fillna("0", inplace=True)
    profile_elite['tokenBalances'] = profile_elite['tokenChangeLogs'].apply(get_token_balance)
    profile_elite['tokenBalanceStd'] = profile_elite['tokenBalances'].apply(np.std)
    Dapps_balance = profile_elite[['_id','tokenBalanceStd']]
    return Dapps_balance

    
def generate_training_data_service(input_path,saving_path):
    profile = pd.read_csv(f"{input_path}/profile.csv")
    transfer_from = pd.read_csv(f"{input_path}/from_transfer_price.csv")
    transfer_to = pd.read_csv(f"{input_path}/to_transfer_price.csv")
    transaction_from = pd.read_csv(f"{input_path}/from_transaction.csv")
    transaction_to = pd.read_csv(f"{input_path}/to_transaction.csv")

    profile_clean= profile.dropna(subset=['balanceChangeLogs'])
    transaction_from = transaction_from.rename(columns={"sending_wallet":"to_wallet","block_timestampHistory":"timestampHistory","value_tuple":"amount_history"})
    transaction_from['contractAddress'] ='0x0000000000000000000000000000000000000000'
    Dapps_from = pd.concat([transfer_from, transaction_from])

    transaction_to = transaction_to.rename(columns={"receiving_wallet":"from_wallet","block_timestampHistory":"timestampHistory","value_tuple":"amount_history"})
    transaction_to['contractAddress'] ='0x0000000000000000000000000000000000000000'
    Dapps_to = pd.concat([transfer_to, transaction_to])

    profile_clean[['tokens','depositChangeLogs','borrowChangeLogs','balanceChangeLogs']] = profile_clean[['tokens','depositChangeLogs','borrowChangeLogs','balanceChangeLogs']].fillna("0")
    profile_clean['tokens'] =profile_clean['tokens'].apply(eval)
    profile_clean['borrowChangeLogs'] =profile_clean['borrowChangeLogs'].apply(eval)
    profile_clean['depositChangeLogs'] =profile_clean['depositChangeLogs'].apply(eval)
    profile_clean['balanceChangeLogs'] =profile_clean['balanceChangeLogs'].apply(eval)

    Dapps_from.rename(columns ={"to_wallet":"interactedWallet"}, inplace=True)
    Dapps_to.rename(columns ={"from_wallet":"interactedWallet"}, inplace=True)
    Dapps_transaction = pd.concat([Dapps_from, Dapps_to])
    Dapps_transaction_clean = Dapps_transaction[Dapps_transaction['wallet'].isin(profile_clean.wallet.unique().tolist())]
    Dapps_transaction_clean['timestampHistory'] = Dapps_transaction_clean['timestampHistory'].apply(eval)
    Dapps_transaction_clean['tokenInteractTimes'] = Dapps_transaction_clean['timestampHistory'].apply(len)
    #frequency
    Dapps_freq = get_freq_features(Dapps_transaction_clean)
    Dapps_value = get_value_features(Dapps_transaction_clean)
    Dapps_balance = get_balance_features(Dapps_transaction_clean, profile_clean)




    ## balance

    ### Training data
    Dapps_freq_value = Dapps_freq.merge(Dapps_value, on='wallet', how ='inner')
    Dapps_training = Dapps_freq_value.merge(Dapps_balance, on='wallet', how='inner')
    Dapps_training = Dapps_training.sort_values('reputationScore', ascending=False)
    df_filtered = remove_outliers_iqr(Dapps_training,['reputationScore'])
    df_sorted = df_filtered.sort_values(by='reputationScore', ascending=False)
    num_observations_to_select = int(0.3 * len(df_sorted))
    balance_threshold = Dapps_training.iloc[num_observations_to_select-1]['reputationScore']
    Dapps_training['label'] = Dapps_training.apply(lambda row: get_label(row, balance_threshold), axis=1)
    Dapps_training.drop("reputationScore", axis=1, inplace = True)
    Dapps_training.to_csv(f"{saving_path}/training_data.csv", index=False)


class GenerateData(BaseJob):
    def __init__(self, direction, importer, exporter, name, index_lst, aave_addresses, max_workers= 4, batch_size=500):
        self.importer = importer
        self.exporter = exporter
        self.name = name
        self.batch_size = batch_size
        self.aave_address = aave_addresses
        self.direction = direction
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
                    aave_transac = {key: aave_users.get(key) for key in transact_lst}
                    aave_balance =  {key: aave_users.get(key) for key in balance_lst}
                    transac_df = get_df(aave_transac)
                    value_df = get_value_features(transac_df)
                    freq_df = get_freq_features(transac_df)
                    balance_df = get_balance_features(pd.DataFrame([aave_balance]))
                    info_df = value_df.merge(freq_df, on='_id',how = 'inner')
                    info_df = info_df.merge(balance_df, on='_id', how='inner')
                    info_dict = info_df.to_dict(orient='records')
                    info_df_lst.extend(info_dict)
                if info_df_lst != []:
                    self.exporter.update_data(name=self.name, data=info_df_lst)
        if self.direction =='search':
            for work in works:
                cursor = self.importer.find({'_id':{ '$nin': self.aave_address}},{'_id':1,'interactedWallet':1,'tokenChangeLogs':1,'balanceChangeLogs':1,'depositChangeLogs':1,'borrowChangeLogs':1})
                transact_lst = ['_id','interactedWallet']
                balance_lst = ['_id','balanceChangeLogs','depositChangeLogs','borrowChangeLogs','tokenChangeLogs']
                info_df_lst = []
                try:
                    for aave_users in cursor[work-self.batch_size: work]:
                        try:
                            aave_transac = {key: aave_users.get(key) for key in transact_lst}
                            aave_balance =  {key: aave_users.get(key) for key in balance_lst}
                            transac_df = get_df(aave_transac)
                            value_df = get_value_features(transac_df)
                            freq_df = get_freq_features(transac_df)
                            balance_df = search_balance_feature(pd.DataFrame([aave_balance]))
                            info_df = value_df.merge(freq_df, on='_id',how = 'inner')
                            info_df = info_df.merge(balance_df, on='_id', how='inner')
                            info_dict = info_df.to_dict(orient='records')
                            info_df_lst.extend(info_dict)
                        except Exception as e:
                            print(e)
                            continue
                except Exception as ex:
                    get_logger(ex)
                    if info_df_lst != []:
                        self.exporter.update_data(name=self.name, data=info_df_lst)
                    continue
                if info_df_lst != []:
                    self.exporter.update_data(name=self.name, data=info_df_lst)

    def _end(self):
        super()._end()



