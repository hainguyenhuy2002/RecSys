import pandas as pd 
import time 

from constants.network_constants import NATIVE_TOKEN
from utils.logger_utils import write_file
from utils.list_dict_utils import flatten_and_concat, rename_key, update_list_of_dict, chunk_list
from utils.history_price_utils import get_daily_timestamp
from utils.upload_utils import update_format
from databases.mongodb_main import MongoDBMain
from databases.postgresql import PostgresDB
from constants.network_constants import Chains

class GetTransactionInfoService():
    def __init__(self, mongo_community, historical_token_price, multichain_transaction, special_wallets, filename: str):
        self.profile_info = list()
        self.mongo_community = mongo_community
        self.historical_token_price = historical_token_price
        self.multichain_transaction = multichain_transaction
        self.special_wallets = special_wallets
        
        ## Get deposit, borrow, balance info
        self.direction = ['from','to']
        self.filename = filename
        self.native = NATIVE_TOKEN
        self.fail_addresses = list()

    def _generate_exchange_info(self, works):
        addresses = list()
        other_lst = list()
        for address in works:
            if (address['address'] not in self.special_wallets) &(address['type']!='contract'):     
                    address_dct = dict()
                    address_dct['chainId'] = address['chainId']
                    address_dct['address'] = address['address']
                    addresses.append(address_dct)
                    other_lst.append(address)
        
        multichain_address = update_list_of_dict(addresses)
    
        multichain_other_fields = update_list_of_dict(other_lst)
        for chain_id, addresses in multichain_address.items():
            if chain_id in self.multichain_transaction:
                chain = Chains.reverse_mapping[chain_id]
                other_info = rename_key(multichain_other_fields[chain_id], 'address','wallet') 
                sending_transfer_info, receiving_transfer_info, transfer_elite_addresses = self._wallet_transfer_info(
                    postgre=PostgresDB(chain_id=chain_id),
                    start_block=self.multichain_transaction[chain_id]['start_block'],
                    end_block=self.multichain_transaction[chain_id]['end_block'],
                    historical_token_price=self.historical_token_price[chain_id],
                    block_timestamp_mappings=self.multichain_transaction[chain_id]['block_timestamp_mappings'],
                    works=addresses
                    ) #postgres

                if len(transfer_elite_addresses)!=0:
                    sending_transaction_info, receiving_transaction_info = self._wallet_transaction_info(
                        mongo_transaction=MongoDBMain(chain=chain),
                        start_date=self.multichain_transaction[chain_id]['start'],
                        end_date=self.multichain_transaction[chain_id]['end'],
                        historical_token_price=self.historical_token_price[chain_id],
                        works=addresses
                    ) #mongo
                    if sending_transaction_info.empty==False:
                        sending_transaction_info['contractAddress'] = self.native
                    if receiving_transaction_info.empty==False:    
                        receiving_transaction_info['contractAddress'] = self.native
                    
                    profiling = pd.concat([sending_transfer_info, sending_transaction_info, receiving_transaction_info, receiving_transfer_info])
                    profiling = profiling.dropna()
                    if (profiling.empty == False) &('contractAddress' in profiling.columns):
                        try:
                            profile_info = profiling.groupby(
                                ['wallet','interactedWallet','contractAddress']) \
                                .agg({"timestampHistory":flatten_and_concat,
                                       "valueInUSDHistory":flatten_and_concat,
                                       "amountHistory":flatten_and_concat}
                                    ).reset_index()
                            profile_infoo = profile_info. \
                                            set_index(['wallet','interactedWallet','contractAddress']). \
                                            apply(lambda x: x.explode()) \
                                            .reset_index()
                            
                            profile_infooo = profile_infoo.groupby(['wallet','interactedWallet','contractAddress', 'timestampHistory']) \
                                                            .agg({
                                                                "valueInUSDHistory":sum,
                                                                "amountHistory":sum}
                                                                ).reset_index()


                                
                            profile_timestamp = profile_info[['wallet','timestampHistory']].copy()
                            profile_max_timestamp = profile_timestamp.groupby('wallet').agg(
                                {"timestampHistory":flatten_and_concat}
                            )
                            profile_max_timestamp['lattestTimestamp'] = profile_max_timestamp['timestampHistory'].apply(lambda x: max(x))
                            max_timestamp = profile_max_timestamp['lattestTimestamp'].to_dict()
                            profile_info_dict = update_format(profile_infooo)
                            dict_lookup = {item['wallet']: item for item in profile_info_dict}
                            for update in other_info:
                                wallet = update['wallet']
                                if (wallet in dict_lookup):
                                    max_time_dct = dict()
                                    tags_dct = dict()
                                    tags_time = dict()
                                    max_time_dct['lattestTimestamp'] = max_timestamp[wallet]
                                    max_time_dct['lattestTags'] = update['tags']
                                    now_time = time.time()
                                    now_daily_time = get_daily_timestamp(int(now_time))
                                    tags_time[f'{now_daily_time}'] = update['tags']
                                    tags_dct['tags'] = tags_time
                                    dict_lookup[wallet].update(update)  # Update in here
                                    dict_lookup[wallet].update(max_time_dct) 
                                    dict_lookup[wallet].update(tags_dct)

                            
                            try:
#                            for job in update_jobs:
                                self.mongo_community.update_data(name=self.profile_info_dict, data=job)
                            except Exception as e:
                                update_jobs = chunk_list(input_list=profile_info_dict, chunk_size=20)
                                for job in update_jobs:
                                    self.mongo_community.update_data(name=self.filename, data=job)
                        except Exception as e:
                            profiling.to_csv(f"data/log_file/address_info/{chain_id}/checking.csv", index=False)
                            print('oh no having error in combinning 2 dataframe')
                            print(e)
                else:
                    self.fail_addresses.extend(addresses)
     

    def _wallet_transaction_info(self, mongo_transaction, start_date, end_date, historical_token_price, works): 
        for direction in self.direction:
            if direction == 'from':
                opposite_direction ='to'
                address_info_lst = mongo_transaction.get_transaction_info(
                    start_date=start_date, 
                    end_date=end_date, 
                    direction=direction, 
                    opposite_direction=opposite_direction, 
                    special_addresses=self.special_wallets, 
                    addresses=works, 
                    price_history=historical_token_price[f'{self.native}']
                    )

                if len(address_info_lst) !=0:
                    addresses_info_df = pd.DataFrame(address_info_lst)
                    wallet_transaction_info = addresses_info_df.groupby(['from_address', 'to_address'])\
                                                                        .agg({"block_timestamp":list,  
                                                                            'amount':list, 
                                                                            "valueInUSD": ['sum', list]})
                    
                    wallet_transaction_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transaction_info.columns]
                    sending_transaction_info = wallet_transaction_info.reset_index()\
                                        .rename(
                                            columns={"from_address": "wallet",
                                                     "to_address":"interactedWallet",
                                                     "block_timestamp_list":"timestampHistory",
                                                     "valueInUSD_list":"valueInUSDHistory", 
                                                     "valueInUSD_sum":"totalValueInUSD", 
                                                     "amount_list":"amountHistory"})
                
                if (len(address_info_lst) ==0 ):
                    sending_transaction_info = pd.DataFrame()

            if direction == 'to':
                opposite_direction ='from'
                address_info_lst = mongo_transaction.get_transaction_info(
                    start_date=start_date, 
                    end_date=end_date, 
                    direction=direction, 
                    opposite_direction=opposite_direction, 
                    special_addresses=self.special_wallets, 
                    addresses=works, 
                    price_history=historical_token_price[f'{self.native}']
                    )

                if len(address_info_lst) !=0:
                    addresses_info_df = pd.DataFrame(address_info_lst)
                    wallet_transaction_info = addresses_info_df.groupby(['from_address', 'to_address'])\
                                                                        .agg({"block_timestamp":list,  
                                                                              'amount':list, 
                                                                              "valueInUSD": ['sum', list]})
                    
                    wallet_transaction_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transaction_info.columns]
                    receiving_transaction_info = wallet_transaction_info.reset_index()\
                                        .rename(
                                            columns={"to_address": "wallet",
                                                     "from_address":"interactedWallet", 
                                                     "block_timestamp_list":"timestampHistory", 
                                                     "valueInUSD_list":"valueInUSDHistory", 
                                                     "valueInUSD_sum":"totalValueInUSD", 
                                                     "amount_list":"amountHistory"})
                    
                if (len(address_info_lst) ==0 ):
                    receiving_transaction_info = pd.DataFrame()

        return sending_transaction_info, receiving_transaction_info


    def _wallet_transfer_info(self, postgre, start_block, end_block, historical_token_price, block_timestamp_mappings, works): 
        for direction in self.direction:
            if direction == 'from':
                opposite_direction ='to'
                wallet_transfer, failed_sender = postgre.query_addresses(
                    addresses=works, 
                    special_addresses=self.special_wallets, 
                    direction= direction, 
                    opposite_direction=opposite_direction, 
                    from_block=start_block, 
                    to_block=end_block, 
                    block_timestamp_mappings=block_timestamp_mappings, 
                    price_history = historical_token_price
                    )
                elite_sender = list(set(works)- set(failed_sender))
                if len(elite_sender) ==0:
                    return  pd.DataFrame(), pd.DataFrame(), []
                else:
                    if len(wallet_transfer)!=0:            
                        transfer_concat = pd.DataFrame(wallet_transfer)
                        transfer_concat = transfer_concat.dropna()
                        transfer_concat = transfer_concat.rename(
                            columns={"value":"amount", 
                                     "contract_address":"contractAddress"}
                                     )
                        wallet_transfer_info = transfer_concat.groupby(
                            ['from_address', 'to_address', 'contractAddress'])  \
                                .agg({"block_number":list, 
                                      'amount':list, 
                                      "valueInUSD": ['sum',list]}
                                    )
                        wallet_transfer_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transfer_info.columns]
                        sending_transfer_info = wallet_transfer_info.reset_index().rename(
                                                columns={"from_address": "wallet",
                                                         "to_address":"interactedWallet", 
                                                         "block_number_list":"timestampHistory", 
                                                         "valueInUSD_list":"valueInUSDHistory",
                                                         "valueInUSD_sum":"totalValueInUSD", 
                                                         "amount_list":"amountHistory"})
                    else:
                        sending_transfer_info = pd.DataFrame()

            if direction =='to':
                opposite_direction = 'from'
                wallet_transfer, failed_borrower = postgre.query_addresses(
                    addresses=elite_sender, 
                    special_addresses=self.special_wallets, 
                    direction= direction, 
                    opposite_direction=opposite_direction, 
                    from_block=start_block, 
                    to_block=end_block, 
                    block_timestamp_mappings=block_timestamp_mappings, 
                    price_history = historical_token_price
                    )
                elite_borrower = list(set(elite_sender)- set(failed_borrower))
                if len(elite_borrower) ==0:
                    return  pd.DataFrame(), pd.DataFrame(), []
                else:
                    if len(wallet_transfer)!=0:            
                        transfer_concat = pd.DataFrame(wallet_transfer)
                        transfer_concat = transfer_concat.dropna()
                        transfer_concat = transfer_concat.rename(columns={"value":"amount", 
                                                                          "contract_address":"contractAddress"})
                        
                        wallet_transfer_info = transfer_concat.groupby(['from_address', 'to_address', 'contractAddress']).\
                                                                agg({"block_number":list, 
                                                                'amount':list, "valueInUSD": ['sum',list]})
                        wallet_transfer_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transfer_info.columns]
                        receiving_transfer_info = wallet_transfer_info.reset_index()\
                                        .rename(columns={"to_address": "wallet",
                                                         "from_address":"interactedWallet", 
                                                         "block_number_list":"timestampHistory",
                                                         "valueInUSD_list":"valueInUSDHistory",            
                                                         "valueInUSD_sum":"totalValueInUSD", 
                                                         "amount_list":"amountHistory"})
                    else: 
                        receiving_transfer_info = pd.DataFrame()

        elite_addresses = list(set(elite_sender).intersection(set(elite_borrower)))
        if sending_transfer_info.empty == False:
            sending_transfer_info = sending_transfer_info[sending_transfer_info['wallet'].isin(elite_addresses)]
        if receiving_transfer_info.empty == False:
            receiving_transfer_info = receiving_transfer_info[receiving_transfer_info['wallet'].isin(elite_addresses)]

        return sending_transfer_info, receiving_transfer_info, elite_addresses
    def _end(self):
        super()._end()
        write_file(f'address_info/', 'fail_addresses.json',self.fail_addresses)

