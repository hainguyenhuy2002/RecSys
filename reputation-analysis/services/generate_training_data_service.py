import json
import os
import pandas as pd 
from multithread_processing.base_job import BaseJob
from utils.logger_utils import get_logger, write_file
from utils.generate_training_utils import get_df, get_balance_features, get_value_features, get_freq_features, search_balance_feature
from constants.network_constants import Chains


class GenerateData(BaseJob):
    def __init__(self, direction, importer, exporter, klg, index_lst, timestamp, dapps_name=None, Dapps_user_addresses=None, max_workers= 4, batch_size=500):
        self.importer = importer
        self.exporter = exporter
        self.klg = klg 
        self.dapps_name = dapps_name
        self.batch_size = batch_size
        self.Dapps_user_addresses = Dapps_user_addresses
        self.direction = direction
        self.timestamp = timestamp
        self.timestamp_str = str(timestamp)
        self.df_lst = []
        super().__init__(work_iterable=index_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        if self.direction =='train':
            for work in works:
                cursor = self.importer.find({'_id':{ '$in': self.Dapps_user_addresses}},{'_id':1,'interactedWallet':1})
                transact_lst = ['_id','interactedWallet']
           #     balance_lst = ['_id','balanceChangeLogs','depositChangeLogs','borrowChangeLogs','tokenChangeLogs']
                info_df_lst = []
                for dapps_users in cursor[work-self.batch_size: work]:
                    dapps_transac = {key: dapps_users.get(key) for key in transact_lst}
                    wallet_id = dapps_transac['_id']
                    chain_id = wallet_id.split('_')[0]
                    klg_cursor = self.klg._db.wallets.find({'_id':f'{wallet_id}'},{'_id':1,
                                                                                   'tokens':1,
                                                                                   'balanceChangeLogs':1,
                                                                                   'depositChangeLogs':1,
                                                                                   'borrowChangeLogs':1,
                                                                                   'tokenChangeLogs':1})

                    #dapps_balance =  {key: dapps_users.get(key) for key in balance_lst}
                    dapps_balance = list(klg_cursor)[0]
                    print(dapps_balance)
                    transac_df = get_df(dapps_transac)
                    transac_df = transac_df[transac_df['timestampHistory']<self.timestamp]
                    balance_df, text = get_balance_features(
                        dapps_name=self.dapps_name,
                        chain_id=chain_id,
                        dapps_balance=dapps_balance, 
                        timestamp=self.timestamp_str
                        )

                    if (transac_df.empty) &(text =='future data'):
                        write_file(
                            folder_direction=f'{self.dapps_name}_train/{self.timestamp}/future_wallet',
                            name='future_addresses.json', 
                            file=dapps_users['_id']
                        )
                        continue

                    elif text =='future data':
                        write_file(
                            folder_direction=f'{self.dapps_name}_train/{self.timestamp}/potential_wallet',
                            name='potential_addresses.json', 
                            file=dapps_users['_id']
                        )
                        continue
                    
                    elif text =='outdated':
                        write_file(
                            folder_direction=f'{self.dapps_name}_train/{self.timestamp}/outdated_wallet',
                            name='outdated_addresses.json', 
                            file=dapps_users['_id']
                        )
                        continue

                    elif text == 'acceptable':
                        value_df = get_value_features(transac_df)
                        freq_df = get_freq_features(transac_df)
                        info_df = value_df.merge(freq_df, on='_id',how = 'inner')
                        info_df = info_df.merge(balance_df, on='_id', how='inner')
                        if info_df.empty == False:
                            self.df_lst.append(info_df)
                        # info_dict = info_df.to_dict(orient='records')
                        # info_df_lst.extend(info_dict)
    
#                if info_df_lst != []:
#                    self.exporter.update_data(name=self.name, data=info_df_lst)

        if self.direction =='search':
            for work in works:
                cursor = self.importer.find({},{'_id':1,'interactedWallet':1})
                transact_lst = ['_id','interactedWallet']
              #  balance_lst = ['_id','balanceChangeLogs','depositChangeLogs','borrowChangeLogs','tokenChangeLogs']
                info_df_lst = []
                try:
                    for dapps_users in cursor[work-self.batch_size: work]:
                        try:
                            dapps_transac = {key: dapps_users.get(key) for key in transact_lst}
                            wallet_id = dapps_transac['_id']
                            klg_cursor = self.klg._db.wallets.find({'_id':f'{wallet_id}'}, 
                                                                   {'_id':1,'balanceInUSD':1,
                                                                    'balanceChangeLogs':1,
                                                                    'balanceInUSD':1})
                            #dapps_balance =  {key: dapps_users.get(key) for key in balance_lst}
                            dapps_balance = list(klg_cursor)[0]
                            transac_df = get_df(dapps_transac)

                            transac_df = transac_df[transac_df['timestampHistory']<self.timestamp]
                            value_df = get_value_features(transac_df)
                            freq_df = get_freq_features(transac_df)
                            balance_df = search_balance_feature(dapps_balance, self.timestamp)
                            info_df = value_df.merge(freq_df, on='_id',how = 'inner')
                            info_df = info_df.merge(balance_df, on='_id', how='inner')
                            if info_df.empty:
                                write_file(
                                    folder_direction=f'search/{self.timestamp}/search',
                                    name='failed_addresses.json', 
                                    file=dapps_users['_id']
                                )
                            else:
                                self.df_lst.append(info_df)
                                # info_dict = info_df.to_dict(orient='records')
                                # info_df_lst.extend(info_dict)
                        except Exception as e:
                            print(e)
                            print(dapps_users)
                            continue
                except Exception as ex:
                    print(ex)
                    # if info_df_lst != []:
                    #     self.exporter.update_data(name=f'{self.chain_name}_{self.timestamp}', data=info_df_lst)
                    continue
                # if info_df_lst != []:
                #     self.exporter.update_data(name=f'{self.chain_name}_{self.timestamp}', data=info_df_lst)

    def _end(self):
        super()._end()
        if self.direction =='train':
            df = pd.concat(self.df_lst).fillna(0)
            if not os.path.exists(f'data/{self.dapps_name}/train'):
                os.makedirs(f'data/{self.dapps_name}/train')
            df.to_parquet(f'data/{self.dapps_name}/train/train_{self.timestamp}.parquet')

        if self.direction =='search':
            df = pd.concat(self.df_lst).fillna(0)
            if not os.path.exists(f'data/search'):
                os.makedirs(f'data/search')
            df.to_parquet(f'data/search/search_{self.timestamp}.parquet')




