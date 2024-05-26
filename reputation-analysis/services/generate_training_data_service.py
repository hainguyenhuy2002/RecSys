import json
import os
import pandas as pd 
from collections import Counter
from multithread_processing.base_job import BaseJob
from utils.logger_utils import get_logger, write_file1, write_file
from utils.generate_training_utils import get_df_v2, get_balance_features, get_value_features, get_freq_features, search_balance_feature, get_only_value_features
from constants.network_constants import Chains
from constants.dapps_tokens_constans import Dapps
from IPython.utils import io

logger = get_logger("Generate training data")

class GenerateData(BaseJob):
    def __init__(self, direction, importer, exporter, klg, index_lst, timestamp, dapps_name=None, Dapps_user_addresses=None, max_workers= 4, batch_size=500):
        self.importer = importer
        self.exporter = exporter
        self.klg = klg 
        self.dapps_name = dapps_name
        self.batch_size = batch_size
        if dapps_name != None:
           self.tokens = Dapps(dapps_name=dapps_name).tokens
        self.Dapps_user_addresses = Dapps_user_addresses
        self.direction = direction
        self.timestamp = timestamp
        self.timestamp_str = str(timestamp)
        self.df_lst = []
        self.token_interact = []
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
                                                                                   'balanceInUSD':1,
                                                                                   'depositInUSD':1,
                                                                                   'borrowInUSD':1,
                                                                                   'balanceChangeLogs':1,
                                                                                   'depositChangeLogs':1,
                                                                                   'borrowChangeLogs':1,
                                                                                   'tokenChangeLogs':1})

                    #dapps_balance =  {key: dapps_users.get(key) for key in balance_lst}
                    dapps_balance = list(klg_cursor)[0]
                    transac_df = get_df_v2(dapps_transac)
                    transac_df = transac_df[transac_df['timestampHistory'].apply(int)<self.timestamp]
                    balance_df, text = get_balance_features(
                        dapps_name=self.dapps_name,
                        chain_id=chain_id,
                        dapps_balance=dapps_balance, 
                        timestamp=self.timestamp_str
                        )

                    if (transac_df.empty) &(text =='future data'):
                        write_file1(
                            folder_direction=f'{self.dapps_name}_train/{self.timestamp}/future_wallet',
                            name='future_addresses.json', 
                            file=dapps_users['_id']
                        )
                        continue

                    elif text =='future data':
                        write_file1(
                            folder_direction=f'{self.dapps_name}_train/{self.timestamp}/potential_wallet',
                            name='potential_addresses.json', 
                            file=dapps_users['_id']
                        )
                        continue
                    
                    elif text =='outdated':
                        write_file1(
                            folder_direction=f'{self.dapps_name}_train/{self.timestamp}/outdated_wallet',
                            name='outdated_addresses.json', 
                            file=dapps_users['_id']
                        )
                        continue

                    elif text == 'acceptable':
                        value_df, tokens_interact = get_value_features(transac_df, chain_id, self.klg)
                        freq_df = get_freq_features(transac_df)
                        info_df = value_df.merge(freq_df, on='_id',how = 'inner')
                        info_df = info_df.merge(balance_df, on='_id', how='inner')
                        if info_df.empty == False:
                            merged_df = info_df.groupby(axis=1, level=0).sum()
                            self.df_lst.append(merged_df)
                            self.token_interact.extend(tokens_interact)
                        # info_df_lst.extend(info_dict)
                        # info_dict = info_df.to_dict(orient='records')
#                if info_df_lst != []:
#                    self.exporter.update_data(name=self.name, data=info_df_lst)

        if self.direction =='search':
            for work in works:
                cursor = self.importer.find({},{'_id':1,'interactedWallet':1})
                transact_lst = ['_id','interactedWallet']
              #  balance_lst = ['_id','balanceChangeLogs','depositChangeLogs','borrowChangeLogs','tokenChangeLogs']
             #   try:
                wallet_id_lst = []
                info_df_lst = []
                for dapps_users in cursor[work-self.batch_size: work]:
                    try:
                        dapps_transac = {key: dapps_users.get(key) for key in transact_lst}
                        wallet_id = dapps_transac['_id']
                        transac_df = get_df_v2(dapps_transac)

                        transac_df = transac_df[transac_df['timestampHistory']. \
                                                apply(int)<self.timestamp]
                        
                        value_df = get_only_value_features(transac_df)  #do not get token value, just avgUSD, totalUSD
                        freq_df = get_freq_features(transac_df)
                        sub_info_df = value_df.merge(freq_df, on='_id',how = 'inner')
                        wallet_id_lst.append(wallet_id)
                        info_df_lst.append(sub_info_df)

                    except Exception as e:
                        print(e)
                        print(dapps_users)
                        continue
                

                klg_cursor = self.klg._db.wallets.find({'_id':{'$in':wallet_id_lst}}, 
                                                                {'_id':1,'balanceInUSD':1,
                                                                'balanceChangeLogs':1})
                cursor_balance_lst =[]
                for klg_cur in klg_cursor:
                    cursor_balance_lst.append(klg_cur)

                dapps_balance = pd.DataFrame(cursor_balance_lst)
                dapps_balance = dapps_balance.fillna(0)
                balance_df = search_balance_feature(dapps_balance, self.timestamp)
                info_df = pd.concat(info_df_lst)
                info_df = info_df.merge(balance_df, on='_id', how='inner')

                if info_df.empty:
                    write_file(
                        folder_direction=f'search/{self.timestamp}/search',
                        name='failed_addresses.json', 
                        file=dapps_users['_id']
                    )
                else:
                    self.df_lst.append(info_df)


             #   except Exception as ex:
            #        print(ex)
                    # if info_df_lst != []:
                    #     self.exporter.update_data(name=f'{self.chain_name}_{self.timestamp}', data=info_df_lst)
            #        continue
                # if info_df_lst != []:
                #     self.exporter.update_data(name=f'{self.chain_name}_{self.timestamp}', data=info_df_lst)

    def _end(self):
        super()._end()
        if self.direction =='train':
            logger.info("Start to training preprocess data ....")
            element_counts = Counter(self.token_interact)
            df_token = pd.DataFrame.from_dict(element_counts, orient='index').reset_index()
            df_token.columns = ['tokens', 'count']
            df_token = df_token.sort_values('count', ascending=False)

            num_chain = len(self.tokens) ## get number of chain that Dapps support
            num_tokens = 50*num_chain
            accept_tokens =  len(df_token.iloc[:num_tokens].tokens.unique().tolist())
            ignore_tokens = df_token.iloc[num_tokens:].tokens.unique().tolist()
            
            preprocessed_df_lst = []
            for sub_df in self.df_lst:
                with io.capture_output() as captured:  # not show warning

                    accepted_columns = set(df_token.iloc[:num_tokens].tokens.unique().tolist()) - set(sub_df.columns) ## accept tokens
                    columns_to_remove = sub_df.columns.intersection(ignore_tokens) ## invalid tokens
                    sub_df['other'] = sub_df[columns_to_remove].sum(axis=1)
                    sub_df = sub_df.drop(columns_to_remove, axis=1)
                    for accept_col in accepted_columns:
                        sub_df[accept_col] = 0
                    preprocessed_df_lst.append(sub_df)

            logger.info(f"Successful preprocess dataframe with {accept_tokens} tokens")
            df = pd.concat(preprocessed_df_lst).fillna(0)
            df = df.reindex(sorted(df.columns), axis=1)

            if not os.path.exists(f'data/{self.dapps_name}/train'):
                os.makedirs(f'data/{self.dapps_name}/train')
            df.to_parquet(f'data/{self.dapps_name}/train/train_{self.timestamp}.parquet')


        if self.direction =='search':
            df = pd.concat(self.df_lst).fillna(0)
            if not os.path.exists(f'data/search'):
                os.makedirs(f'data/search')
            df.to_parquet(f'data/search/search_{self.timestamp}.parquet')




