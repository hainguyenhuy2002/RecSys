import pandas as pd 
import numpy as np
from utils.logger_utils import get_logger
from services.one_month_profile_service import GetWalletInfo
from constants.time_constants import TimeConstants
from databases.mongodb_entity import MongoDBEntity
from constants.network_constants import Chains

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
    Dapps_transaction_clean_info = Dapps_transaction_clean.groupby(['wallet','interactedWallet','contract_address']) \
                                    .agg({'timestamp_history':flatten_and_concat,'token_interact_times':'sum',}).reset_index()
    Dapps_transaction_clean_info['address_interact_times'] = Dapps_transaction_clean_info['timestamp_history'].apply(len)
    Dapps_transaction_clean_info_token = Dapps_transaction_clean_info.groupby(['wallet','contract_address']) \
                                    .agg({'token_interact_times':'sum'}).reset_index()
    Dapps_transaction_clean_info_tokens = Dapps_transaction_clean_info_token.groupby('wallet') \
                                    .agg({'contract_address':'count', 'token_interact_times': tuple}).reset_index()
    Dapps_transaction_clean_info_address = Dapps_transaction_clean_info.groupby(['wallet','interactedWallet']) \
                                    .agg({'address_interact_times':'sum'}).reset_index()
    Dapps_transaction_clean_info_addresses = Dapps_transaction_clean_info_address.groupby('wallet') \
                                    .agg({'interactedWallet':'count', 'address_interact_times': tuple}).reset_index()
    Dapps_freq_info = Dapps_transaction_clean_info.groupby('wallet') \
                                    .agg({'timestamp_history':flatten_and_concat}).reset_index()
    
    Dapps_freq_info = Dapps_freq_info.merge(Dapps_transaction_clean_info_tokens, how='inner', on='wallet')
    Dapps_freq_info = Dapps_freq_info.merge(Dapps_transaction_clean_info_addresses, how='inner', on='wallet')
    Dapps_freq_info['noTransaction'] = Dapps_freq_info['timestamp_history'].apply(len)
    Dapps_freq_info['addressTimeStd'] = Dapps_freq_info['address_interact_times'].apply(lambda row: np.std(row))
    Dapps_freq_info['tokenTimeStd'] = Dapps_freq_info['token_interact_times'].apply(lambda row: np.std(row))
    Dapps_freq_info.rename(columns = {"contract_address":"numInteractedToken","interactedWallet":"numInteractedWallet"}, inplace = True)
    Dapps_freq = Dapps_freq_info[['wallet','numInteractedToken','numInteractedWallet','addressTimeStd','tokenTimeStd','noTransaction']]
    return Dapps_freq

def get_value_features(Dapps_transaction_clean):
    #valueInUSD
    Dapps_transaction_clean['valueInUSD_history'] = Dapps_transaction_clean['valueInUSD_history'].apply(eval)

    Dapps_transaction_clean['interactedTokens']  = Dapps_transaction_clean['contract_address']
    Dapps_token_transfer = Dapps_transaction_clean.groupby(['wallet','interactedTokens']) \
                                    .agg({"valueInUSD_history":flatten_and_concat}).reset_index()
    Dapps_token_transfer['totalInUSD'] = Dapps_token_transfer['valueInUSD_history'].apply(sum)
    Dapps_token_transfer['medInUSD'] = Dapps_token_transfer['valueInUSD_history'].apply(np.median)
    Dapps_tokens = Dapps_token_transfer.pivot_table(values=['totalInUSD','medInUSD'], index='wallet', \
                                    columns='interactedTokens', aggfunc='sum', fill_value = 0) \
                                    .reset_index()
    column_lst = ['wallet']
    column_lst.extend(['{}_{}'.format(col[0], col[1]) for col in Dapps_tokens.columns if col[0]!='wallet'])
    Dapps_tokens.columns = column_lst
    Dapps_value_transfer = Dapps_transaction_clean.groupby(['wallet']) \
                                    .agg({"valueInUSD_history":flatten_and_concat}).reset_index()
    Dapps_value_transfer['totalUSDTransfer'] = Dapps_value_transfer['valueInUSD_history'].apply(sum)
    Dapps_value_transfer['avgUSDTransfer'] = Dapps_value_transfer['valueInUSD_history'].apply(np.median)
    Dapps_value = Dapps_value_transfer[['wallet','totalUSDTransfer','avgUSDTransfer']] \
                                    .merge(Dapps_tokens, on ='wallet',how='inner')
    return Dapps_value


def get_balance_features(Dapps_transaction_clean, profile_clean):
    #balance
    elite_wallets = Dapps_transaction_clean.wallet.unique().tolist()
    profile_elite = profile_clean[profile_clean['wallet'].isin(elite_wallets)]
    profile_elite['tokenChangeLogs'].fillna("0", inplace=True)
    profile_elite['tokenChangeLogs'] = profile_elite['tokenChangeLogs'].apply(eval)

    profile_elite['tokenBalances'] = profile_elite['tokenChangeLogs'].apply(get_token_balance)
    profile_elite['aaveBalance'] = profile_elite['tokenChangeLogs'].apply(get_aave_balance)
    profile_elite['overallBalance'] = profile_elite['balanceChangeLogs'].apply(get_balance)
    profile_elite['aaveAvgDeposit'] = profile_elite['depositChangeLogs'].apply(average_value)
    profile_elite['aaveAvgBorrow'] = profile_elite['borrowChangeLogs'].apply(average_value)
    profile_elite['reputationScore'] = (profile_elite['aaveBalance'] + profile_elite['aaveAvgDeposit']+ profile_elite['aaveAvgBorrow'])/3
    profile_elite['tokenBalanceStd'] = profile_elite['tokenBalances'].apply(np.std)
    Dapps_balance = profile_elite[['wallet','tokenBalanceStd','overallBalance','reputationScore']]
    return Dapps_balance
    
def generate_training_data_service(input_path,saving_path):
    profile = pd.read_csv(f"{input_path}/profile.csv")
    transfer_from = pd.read_csv(f"{input_path}/from_transfer_price.csv")
    transfer_to = pd.read_csv(f"{input_path}/to_transfer_price.csv")
    transaction_from = pd.read_csv(f"{input_path}/from_transaction.csv")
    transaction_to = pd.read_csv(f"{input_path}/to_transaction.csv")

    profile_clean= profile.dropna(subset=['balanceChangeLogs'])
    transaction_from = transaction_from.rename(columns={"sending_wallet":"to_wallet","block_timestamp_history":"timestamp_history","value_tuple":"amount_history"})
    transaction_from['contract_address'] ='0x0000000000000000000000000000000000000000'
    Dapps_from = pd.concat([transfer_from, transaction_from])

    transaction_to = transaction_to.rename(columns={"receiving_wallet":"from_wallet","block_timestamp_history":"timestamp_history","value_tuple":"amount_history"})
    transaction_to['contract_address'] ='0x0000000000000000000000000000000000000000'
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
    Dapps_transaction_clean['timestamp_history'] = Dapps_transaction_clean['timestamp_history'].apply(eval)
    Dapps_transaction_clean['token_interact_times'] = Dapps_transaction_clean['timestamp_history'].apply(len)
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
