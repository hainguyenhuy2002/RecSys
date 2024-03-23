import json
import pandas as pd 
from multithread_processing.base_job import BaseJob
from typing import List
from constants.network_constants import Chains
def flatten_and_concat(tuples):
    flattened = [item for sublist in tuples for item in sublist]
    return flattened

def update_format(data):
    result = {}
    for wallet, interacted_wallet, contractAddress, timestamp_history, value_history, amount_history in zip(
        data['wallet'],
        data['interactedWallet'],
        data['contractAddress'],
        data['timestampHistory'],
        data['valueInUSDHistory'],
        data['amountHistory']
    ):
        if wallet not in result:
            result[wallet] = {'interactedWallet': {}}
        if interacted_wallet not in result[wallet]['interactedWallet']:
            result[wallet]['interactedWallet'][interacted_wallet] = {'contractAddress': {}}
        if contractAddress not in result[wallet]['interactedWallet'][interacted_wallet]['contractAddress']:
            result[wallet]['interactedWallet'][interacted_wallet]['contractAddress'][contractAddress] = {
                'timestampHistory': timestamp_history,
                'valueInUSDHistory': value_history,
                'amountHistory': amount_history
            }

    final_result = [{'_id':wallet, 'wallet': wallet, **data} for wallet, data in result.items()]
    return final_result

class GetWalletTransactionTransfer(BaseJob):
    def __init__(self, chain, mongo_transaction, postgres, exporter, historical_token_price, block_timestamp_mappings, special_wallets, wallets_list: list, filename: str, start_date, end_date, start_block, end_block,
                 max_workers= 4, batch_size=500, sources: List[str] = None):
        self.profile_info = list()
    
        self.chain = chain
        self.mongo_transaction = mongo_transaction
        self.postgres = postgres
        self.exporter =exporter
        self.historical_token_price = historical_token_price
        self.block_timestamp_mappings = block_timestamp_mappings
        self.special_wallets  = special_wallets
        # self.reputation_df = reputation_df

        self.start_date = start_date
        self.end_date = end_date
        self.start_block = start_block
        self.end_block = end_block
        self.direction = ['from','to']
        self.filename = filename
    
        if not sources:
            sources = ['mongo', 'postgres']
        self.sources = sources
        self.chain_id = Chains.mapping[chain]

        super().__init__(work_iterable=wallets_list,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):

        sending_transaction_info, receiving_transaction_info, elite_addresses = self._wallet_transaction_info(works=works) ##mongo
        if len(elite_addresses)!=0:
            sending_transfer_info, receiving_transfer_info = self._wallet_transfer_info(works=elite_addresses)#postgres
            sending_transaction_info['contractAddress'] = '0x0000000000000000000000000000000000000000'
            receiving_transaction_info['contractAddress'] = '0x0000000000000000000000000000000000000000'
            profiling = pd.concat([sending_transfer_info, sending_transaction_info, receiving_transaction_info, receiving_transfer_info])
            if profiling.empty == False:
                profile_info = profiling.groupby(['wallet','interactedWallet','contractAddress']).agg({"timestampHistory":flatten_and_concat, "valueInUSDHistory":flatten_and_concat,"amountHistory":flatten_and_concat}).reset_index()
                profile_info_dict = update_format(profile_info)
                self.exporter.update_data(name=self.filename, data=profile_info_dict)
        ##profile_info = profile_info.groupby(['wallet','interactedWallet'])[[col for col in profile_info.columns if col not in ['wallet','interactedWallet']]].agg(lambda x: list(x)).reset_index()
        #profile_info = profile_info.groupby('wallet')[[col for col in profile_info.columns if col !='wallet']].agg(lambda x: list(x)).reset_index()

#        self.profile_info.append(profile_info)


    def _wallet_transaction_info(self, works): 
        for direction in self.direction:
            if direction == 'from':
                opposite_direction ='to'
                address_info_lst, sending_failed_addresses = self.mongo_transaction.get_transaction_info(start_date=self.start_date, end_date=self.end_date, direction=direction, 
                                                                               opposite_direction=opposite_direction, special_addresses=self.special_wallets, addresses=works, price_history=self.historical_token_price[f'{self.chain}'])
                sending_elite_addresses = list(set(works)- set(sending_failed_addresses))
                if len(sending_elite_addresses) ==0:
                    return  pd.DataFrame(), pd.DataFrame(), []
                if len(address_info_lst) !=0:
                    addresses_info_df = pd.DataFrame(address_info_lst)
                    wallet_transaction_info = addresses_info_df.groupby(['from_address', 'to_address']).agg({"block_timestamp":tuple,  'amount':tuple, "valueInUSD": ['sum', tuple]})
                    wallet_transaction_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transaction_info.columns]
                    sending_transaction_info = wallet_transaction_info.reset_index().rename(columns={"from_address": "wallet","to_address":"interactedWallet", "block_timestamp_tuple":"timestampHistory", 
                                                                                                     "valueInUSD_tuple":"valueInUSDHistory", "valueInUSD_sum":"totalValueInUSD", "amount_tuple":"amountHistory"})
                if (len(address_info_lst) ==0 ) &(len(sending_elite_addresses)!=0):
                    print(works)
                    sending_transaction_info = pd.DataFrame()

            if direction == 'to':
                opposite_direction ='from'
                address_info_lst, receiving_failed_addresses = self.mongo_transaction.get_transaction_info(start_date=self.start_date, end_date=self.end_date, direction=direction, 
                                                                               opposite_direction=opposite_direction, special_addresses=self.special_wallets, addresses=sending_elite_addresses, price_history=self.historical_token_price[f'{self.chain}'])
                receiving_elite_addresses = list(set(works)- set(receiving_failed_addresses))

                if len(receiving_elite_addresses) ==0:
                    return  pd.DataFrame(), pd.DataFrame(), []
                if len(address_info_lst) !=0:
                    addresses_info_df = pd.DataFrame(address_info_lst)
                    wallet_transaction_info = addresses_info_df.groupby(['from_address', 'to_address']).agg({"block_timestamp":tuple,  'amount':tuple, "valueInUSD": ['sum', tuple]})
                    wallet_transaction_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transaction_info.columns]
                    receiving_transaction_info = wallet_transaction_info.reset_index().rename(columns={"to_address": "wallet","from_address":"interactedWallet", "block_timestamp_tuple":"timestampHistory",  
                                                                                                       "valueInUSD_tuple":"valueInUSDHistory", "valueInUSD_sum":"totalValueInUSD", "amount_tuple":"amountHistory"})
                if (len(address_info_lst) ==0 ) &(len(receiving_elite_addresses)!=0):
                    print(works)

                    receiving_transaction_info = pd.DataFrame()

        elite_addresses = list(set(sending_elite_addresses).intersection(set(receiving_elite_addresses)))
        if sending_transaction_info.empty == False:
            sending_transaction_info = sending_transaction_info[sending_transaction_info['wallet'].isin(elite_addresses)]
        if receiving_transaction_info.empty == False:
            receiving_transaction_info = receiving_transaction_info[receiving_transaction_info['wallet'].isin(elite_addresses)]
        return sending_transaction_info, receiving_transaction_info, elite_addresses


    def _wallet_transfer_info(self, works): 
        for direction in self.direction:
            if direction == 'from':
                opposite_direction ='to'
                wallet_transfer = self.postgres.query_addresses(addresses=works, special_addresses=self.special_wallets, direction= direction, opposite_direction=opposite_direction, from_block=self.start_block, 
                                                                to_block=self.end_block, chain_id=self.chain_id, block_timestamp_mappings=self.block_timestamp_mappings, price_history = self.historical_token_price)
                if len(wallet_transfer)!=0:            
                    transfer_concat = pd.DataFrame(wallet_transfer)
                    transfer_concat = transfer_concat.dropna()
                    transfer_concat = transfer_concat.rename(columns={"value":"amount", "contract_address":"contractAddress"})
                    wallet_transfer_info = transfer_concat.groupby(['from_address', 'to_address', 'contractAddress']).agg({"block_number":tuple, 'amount':tuple, "valueInUSD": ['sum',tuple]})
                    wallet_transfer_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transfer_info.columns]
                    sending_transfer_info = wallet_transfer_info.reset_index().rename(columns={"from_address": "wallet","to_address":"interactedWallet", "block_number_tuple":"timestampHistory", 
                                                                                                "valueInUSD_tuple":"valueInUSDHistory", "valueInUSD_sum":"totalValueInUSD", "amount_tuple":"amountHistory"})
                else:
                    sending_transfer_info = pd.DataFrame()
            if direction =='to':
                opposite_direction = 'from'
                wallet_transfer = self.postgres.query_addresses(addresses=works, special_addresses=self.special_wallets, direction= direction, opposite_direction=opposite_direction, from_block=self.start_block, 
                                                                to_block=self.end_block, chain_id=self.chain_id, block_timestamp_mappings=self.block_timestamp_mappings, price_history = self.historical_token_price)
                if len(wallet_transfer)!=0:            
                    transfer_concat = pd.DataFrame(wallet_transfer)
                    transfer_concat = transfer_concat.dropna()
                    transfer_concat = transfer_concat.rename(columns={"value":"amount", "contract_address":"contractAddress"})
                    wallet_transfer_info = transfer_concat.groupby(['from_address', 'to_address', 'contractAddress']).agg({"block_number":tuple, 'amount':tuple, "valueInUSD": ['sum',tuple]})
                    wallet_transfer_info.columns = ['{}_{}'.format(col[0], col[1]) for col in wallet_transfer_info.columns]
                    receiving_transfer_info = wallet_transfer_info.reset_index().rename(columns={"to_address": "wallet","from_address":"interactedWallet", "block_number_tuple":"timestampHistory",
                                                                                                  "valueInUSD_tuple":"valueInUSDHistory", "valueInUSD_sum":"totalValueInUSD", "amount_tuple":"amountHistory"})
                else: 
                    receiving_transfer_info = pd.DataFrame()
        return sending_transfer_info, receiving_transfer_info
    def _end(self):
        super()._end()
