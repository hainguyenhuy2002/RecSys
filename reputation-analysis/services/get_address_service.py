import json
import os
from datetime import datetime, timedelta
import calendar
from pymongo import MongoClient
import pandas as pd
from typing import Dict, Set, List
from multithread_processing.base_job import BaseJob
from utils.logger_utils import get_logger

class GetAddress(BaseJob):
    def __init__(self, importer, arangoDb, exporter, hot_wallets, chain_id, name, flagged_lst: list, max_workers= 4, batch_size=500):
        self.mongo_klg = importer
        self.exporter = exporter
        self.arangoDb = arangoDb
        self.hot_wallets = hot_wallets
        self.chain_id = chain_id
        self.name = name

        now = datetime.now()
        three_months_ago = now - timedelta(days=90)
        self.three_months_ago = calendar.timegm(three_months_ago.timetuple())
        super().__init__(work_iterable=flagged_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        for work in works:
            wallet_lst: List[Dict] = list()
          #  wallets_name = []
            try:
                query =  {"flagged":work, "chainId":f"{self.chain_id}", "balanceChangeLogs":{"$exists":"True"}, "balanceInUSD":{"$gt":0}}
                wallets = self.mongo_klg.find(query,{'_id':1,'flagged':1,'balanceChangeLogs':1,'address':1,'tokenChangeLogs':1,'type':1, 
                                                        'balanceInUSD':1,'tags':1,'depositChangeLogs':1,'depositInUSD':1,'borrowChangeLogs':1,
                                                            'borrowInUSD':1, 'lendings':1,'createdAt':1,'theFirstToTimestamp':1,
                                                                'theFirstFromTimestamp':1, 'dailyAllTransactions':1, 'lastTokenInteractedAt':1, 'dailyAllTransactions': 1})
                for wallet in wallets:
                    if wallet in self.hot_wallets:
                        continue
                    else:
                        if 'dailyAllTransactions' in wallet:
                            numTransaction = sum(value for key, value in wallet['dailyAllTransactions'].items() if key >= str(self.three_months_ago))
                            if numTransaction < 5000:
                                wallet['numTransaction'] = numTransaction

                                if 'type' not in wallet:
                                    wallet['type'] = 0
                                wallet_lst.append(wallet)
                if len(wallet_lst) !=0:
                    # wallet_sent_receive = self.arangoDb.get_num_send_receive(wallets_name)
                    # sent_receive_df = pd.DataFrame(wallet_sent_receive)
                    # sent_receive_df = sent_receive_df.fillna(0)
                    # address_df = pd.DataFrame(wallet_lst)
                    # final_df = address_df.merge(sent_receive_df, on='address', how='inner')
                    # final_df = final_df[(final_df['numberSent']<=200) & (final_df['numberReceived']<=200)]
                    # address_info =final_df.to_dict(orient='records') 
                    self._export_users_available(wallet_lst= wallet_lst, name=self.name)
            except Exception as e:
                print(e)
                continue
    def _export_users_available(self, wallet_lst,name):
        #self.exporter._db[f"{name}"].bulk_write(wallet_lst)
        self.exporter.update_data(name=name, data=wallet_lst)
    def _end(self):
        self.batch_executor.shutdown()


    