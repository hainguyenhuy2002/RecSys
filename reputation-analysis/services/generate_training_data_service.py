import json
import os
import time
import pandas as pd 
from IPython.utils import io
from collections import Counter
from utils.time_utils import round_timestamp
from utils.token_utils import get_token_type
from constants.network_constants import Chains
from constants.dapps_tokens_constans import Dapps
from constants.time_constants import TimeConstants
from multithread_processing.base_job import BaseJob
from utils.logger_utils import get_logger, write_file1, write_file
from utils.generate_training_utils import get_df_v2, get_balance_features, get_value_features, get_freq_features, search_balance_feature, get_only_value_features

logger = get_logger("Generate training data")

class GenerateData(BaseJob):
    def __init__(self, direction, importer, exporter, klg, index_lst, timestamp, name, batch, tags=None, interacted_addresses=None, lending_tags=list(), dapps_name=None, max_workers=4, batch_size=500):
        self.importer = importer
        self.exporter = exporter
        self.klg = klg 
        self.train_id = []
        self.interacted_addresses = interacted_addresses
        self.name = name #name of collection
        self.dapps_name = dapps_name #name of dapps to create train data
        self.batch = batch ## batch to upate in mongodb
        self.max_workers = max_workers
        self.batch_size = batch_size
        if dapps_name != None:
           self.tokens = Dapps(dapps_name=dapps_name).tokens
        self.direction = direction
        self.timestamp = timestamp
        self.timestamp_str = str(timestamp)
        self.df_lst = []
        self.token_interact = []
        self.lending_tags = lending_tags
        self.tags = tags
        super().__init__(work_iterable=index_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)
        
        native_tokens, stable_tokens, top_tokens, other_tokens = get_token_type(MongoDB=exporter, MongoDBEntity=klg)
        self.token_lst = [native_tokens, stable_tokens, top_tokens, other_tokens]
        self.exists_exporter = self.exporter._db.list_collection_names()

    def _execute_batch(self, works):
        if self.direction =='train':
            timestamp_str = str(time.time())
            klg_cursor = self.klg._db.wallets.find({'_id':{'$in':works}},{'_id':1,
                                                                                'tokens':1,
                                                                                'balanceInUSD':1,
                                                                                'depositInUSD':1,
                                                                                'borrowInUSD':1,
                                                                                'balanceChangeLogs':1,
                                                                                'depositChangeLogs':1,
                                                                                'borrowChangeLogs':1,
                                                                                'tokenChangeLogs':1,
                                                                                'chainId':1,
                                                                                'tags':1})
            for cur in klg_cursor:
                balance_df = get_balance_features(
                    dapps_name=self.dapps_name,
                    lending_tags=self.lending_tags,
                    dapps_balance=cur, 
                    timestamp=timestamp_str
                    )
                
                balance_df['batch'] = self.batch
                balance_df['projectId'] = self.dapps_name
                balance_df['addressId']  = balance_df['_id']
                balance_df['_id'] = balance_df['_id'] + '_' + balance_df['projectId']+'_' + balance_df['batch'].apply(str)
                id_lst = balance_df[balance_df['reputationScore']>0].addressId.unique().tolist()
                self.train_id.extend(id_lst)

                update_train = balance_df.to_dict(orient='records')

            self.exporter.update_data(name=self.name, data=update_train)

        if self.direction =='train localization':
            local_wallets = []
            cursor = self.importer.find({'flagged':{'$in':works}, 'latestTags':{'$nin':self.tags}},{'_id':1,'interactedWallet':1})

            for cur in cursor:
                for wallet, _ in cur['interactedWallet'].items():
                    if wallet in self.interacted_addresses:
                        local_wallets.append(cur['_id'])
                        break

            if len(local_wallets) != 0:
                df_local_wallets = pd.DataFrame()
                df_local_wallets['addressId'] = local_wallets
                df_local_wallets['reputationSbalance_df'] = 0
                df_local_wallets['batch'] = self.batch
                df_local_wallets['projectId'] = self.dapps_name
                df_local_wallets['_id'] = df_local_wallets['addressId'] + '_' + df_local_wallets['projectId'] + df_local_wallets['batch'].apply(str)
                update_train = df_local_wallets.to_dict(orient='records')
                self.exporter.update_data(name=self.name, data=update_train)



        if self.direction =='search first':
            time_predict = time.time() - TimeConstants.DAYS_2
            time_train = time_predict - self.timestamp
            cursor = self.importer.find({'flagged':{'$in':works}},{'_id':1,'interactedWallet':1})
            transact_lst = ['_id','interactedWallet']
            wallet_id_lst = []
            lst_train = []
            lst_predict = []
            #logger.info('start to process value and frequency features')
            for dapps_users in cursor:
                try:
                    dapps_transac = {key: dapps_users.get(key) for key in transact_lst}
                    wallet_id = dapps_transac['_id']
                    prep_df = get_df_v2(data=dapps_transac, token_lst=self.token_lst)
                    transac_df_predict = prep_df[prep_df['timestampHistory'].apply(int)>= time_predict - 2*TimeConstants.DAYS_31]
                    lst_predict.append(transac_df_predict)

                    transac_df_train = prep_df[(prep_df['timestampHistory']. \
                                            apply(int)<=time_train) &((prep_df['timestampHistory']. \
                                            apply(int)>=time_train - 2*TimeConstants.DAYS_31))]
                    
                    wallet_id_lst.append(wallet_id)
                    if transac_df_train.empty == False:
                        lst_train.append(transac_df_train)

                except Exception as e:
                    print(e)
                    continue
            
            #logger.info('start to process balance features')

            klg_cursor = self.klg._db.wallets.find({'_id':{'$in':wallet_id_lst}}, 
                                                            {'_id':1,'balanceInUSD':1,
                                                            'balanceChangeLogs':1})
            cursor_balance_lst =[]
            for klg_cur in klg_cursor:
                cursor_balance_lst.append(klg_cur)

            dapps_balance = pd.DataFrame(cursor_balance_lst)
            dapps_balance_predict = dapps_balance.fillna(0).copy()

            balance_df_predict = search_balance_feature(dapps_balance_predict, round_timestamp(time_predict))


            info_predict = pd.concat(lst_predict)
            value_df_predict = get_value_features(info_predict) 
            freq_df_predict = get_freq_features(info_predict)
            freq_value_predict = value_df_predict.merge(freq_df_predict, on='_id',how = 'inner')
            df_predict = freq_value_predict.merge(balance_df_predict, on='_id', how='inner')
            df_predict['batch'] = self.batch +1
            df_predict['addressId'] = df_predict['_id']
            df_predict['_id'] = df_predict['_id'] + '_' + df_predict['batch'].apply(str)
            update_predict = df_predict.to_dict(orient='records')
            #logger.info('start to update data')

            self.exporter.update_data(name=self.name, data=update_predict)

            if len(lst_train)>0:
                dapps_balance_train = dapps_balance.fillna(0).copy()
                balance_df_train = search_balance_feature(dapps_balance_train, round_timestamp(time_train))
                
                info_train = pd.concat(lst_train)
                value_df_train = get_value_features(info_train) 
                freq_df_train = get_freq_features(info_train)
                freq_value_train = value_df_train.merge(freq_df_train, on='_id',how = 'inner')
                df_train = freq_value_train.merge(balance_df_train, on='_id', how='inner')
                df_train['batch'] = self.batch
                df_train['addressId'] = df_train['_id']
                df_train['_id'] = df_train['_id'] + '_' + df_train['batch'].apply(str)
                
                update_train = df_train.to_dict(orient='records')
                self.exporter.update_data(name=self.name, data=update_train)

        if self.direction =='search continue':
            time_predict = time.time() - TimeConstants.DAYS_2
            cursor = self.importer.find({'flagged':{'$in':works}},{'_id':1,'interactedWallet':1})
            transact_lst = ['_id','interactedWallet']
            wallet_id_lst = []
            lst_predict = []
            for dapps_users in cursor:
                try:
                    dapps_transac = {key: dapps_users.get(key) for key in transact_lst}
                    wallet_id = dapps_transac['_id']
                    prep_df = get_df_v2(data=dapps_transac, token_lst=self.token_lst)
                    transac_df_predict = prep_df[prep_df['timestampHistory'].apply(int)>= time_predict - 2*TimeConstants.DAYS_31]
                    #transac_df_predict = get_df_v2(data=dapps_transac, token_lst=self.token_lst)
                    lst_predict.append(transac_df_predict)
                    wallet_id_lst.append(wallet_id)
    
                except Exception as e:
                    print(e)
                    continue
            
            klg_cursor = self.klg._db.wallets.find({'_id':{'$in':wallet_id_lst}}, 
                                                            {'_id':1,'balanceInUSD':1,
                                                            'balanceChangeLogs':1})
            cursor_balance_lst =[]
            for klg_cur in klg_cursor:
                cursor_balance_lst.append(klg_cur)

            dapps_balance = pd.DataFrame(cursor_balance_lst)
            dapps_balance_predict = dapps_balance.fillna(0).copy()

            balance_df_predict = search_balance_feature(dapps_balance_predict, round_timestamp(time_predict))


            info_predict = pd.concat(lst_predict)
            value_df_predict = get_value_features(info_predict) 
            freq_df_predict = get_freq_features(info_predict)
            freq_value_predict = value_df_predict.merge(freq_df_predict, on='_id',how = 'inner')
            df_predict = freq_value_predict.merge(balance_df_predict, on='_id', how='inner')
            df_predict['batch'] = self.batch +1
            df_predict['addressId'] = df_predict['_id']
            df_predict['_id'] = df_predict['_id'] + '_' + df_predict['batch'].apply(str)
            update_predict = df_predict.to_dict(orient='records')
         #   logger.info('start to update data')
            self.exporter.update_data(name=self.name, data=update_predict)

    def _end(self):
        super()._end()

        if self.direction == 'train':
            train_id =self.train_id
            largest_flag = self.exporter.get_largest_flag(db='wallet_exchanges') +1
            flagged_lst = [i for i in range(1, largest_flag)]
            num_flags = len(flagged_lst)
            dapps_tags = Dapps(dapps_name=self.dapps_name).tags


            training_cursor = self.importer.find({'_id':{'$in':train_id}})  
            interacted_addresses = []
            for cur in training_cursor:

                interacted_addresses.extend(list(cur['interactedWallet'].keys()))
            interacted_addresses = list(set(interacted_addresses))

            logger.info(f"start to localization with {num_flags} flags")
            ## localiza†ion
            job2 = GenerateData(importer=self.importer, 
                            exporter=self.exporter, 
                            klg=self.klg,
                            dapps_name=self.dapps_name, 
                            direction='train localization', 
                            index_lst=flagged_lst, 
                            interacted_addresses=interacted_addresses,
                            tags=dapps_tags,
                            timestamp=self.timestamp, 
                            name=self.name,
                            batch=self.batch,
                            max_workers=self.max_workers, 
                            batch_size=self.batch_size)
            job2.run()

    








        #     logger.info("Start to training preprocess data ....")
        #     # element_counts = Counter(self.token_interact)
        #     # df_token = pd.DataFrame.from_dict(element_counts, orient='index').reset_index()
        #     # df_token.columns = ['tokens', 'count']
        #     # df_token = df_token.sort_values('count', ascending=False)

        #     # num_chain = len(self.tokens) ## get number of chain that Dapps support
        #     # num_tokens = 50*num_chain
        #     # accept_tokens =  len(df_token.iloc[:num_tokens].tokens.unique().tolist())
        #     # ignore_tokens = df_token.iloc[num_tokens:].tokens.unique().tolist()
            
        #     # preprocessed_df_lst = []
        #     # for sub_df in self.df_lst:
        #     #     with io.capture_output() as captured:  # not show warning

        #     #         accepted_columns = set(df_token.iloc[:num_tokens].tokens.unique().tolist()) - set(sub_df.columns) ## accept tokens
        #     #         columns_to_remove = sub_df.columns.intersection(ignore_tokens) ## invalid tokens
        #     #         sub_df['other'] = sub_df[columns_to_remove].sum(axis=1)
        #     #         sub_df = sub_df.drop(columns_to_remove, axis=1)
        #     #         for accept_col in accepted_columns:
        #     #             sub_df[accept_col] = 0
        #     #         preprocessed_df_lst.append(sub_df)

        #     # logger.info(f"Successful preprocess dataframe with {accept_tokens} tokens")
        #     df = pd.concat(self.df_lst).fillna(0)
        #     df = df.reindex(sorted(df.columns), axis=1)

        #     if not os.path.exists(f'data/modeling/{self.dapps_name}/train'):
        #         os.makedirs(f'data/modeling/{self.dapps_name}/train')
        #     df.to_parquet(f'data/modeling/{self.dapps_name}/train/train_{self.timestamp}.parquet')


        # if self.direction =='search':
        #     df = pd.concat(self.df_lst).fillna(0)
        #     if not os.path.exists(f'data/modeling/search'):
        #         os.makedirs(f'data/modeling/search')
        #     df.to_parquet(f'data/modeling/search/search_{self.timestamp}.parquet')




