import os
import json
import calendar
import pandas as pd
from pymongo import MongoClient
from typing import Dict, Set, List
from datetime import datetime, timedelta
from utils.logger_utils import get_logger
from utils.list_dict_utils import chunk_list
from multithread_processing.base_job import BaseJob



class GetAddress(BaseJob):
    def __init__(self, importer, exporter, hot_wallets, name, wallets_per_job, exchange_service, flagged_lst: list, max_workers= 4, batch_size=500):
        self.mongo_klg = importer
        self.exporter = exporter
        self.hot_wallets = hot_wallets
        self.name = name
        self.wallets_per_job = wallets_per_job
        self.exchange_service = exchange_service
        now = datetime.now()
        three_months_ago = now - timedelta(days=90)
        self.three_months_ago = calendar.timegm(three_months_ago.timetuple())
        super().__init__(work_iterable=flagged_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        for work in works:
            wallet_lst: List[Dict] = list()
            query =  {"flagged":work, "balanceInUSD":{"$exists":"True"}, "balanceInUSD":{"$gt":0}}
            wallets = self.mongo_klg.find(query,{'_id':1,
                                                'chainId':1,   
                                                'address':1,
                                                'type':1,
                                                'tags':1,
                                                'dailyAllTransactions':1})
            for wallet in wallets:
                if wallet['address'] in self.hot_wallets:
                    continue
                else:
                    if 'dailyAllTransactions' in wallet:
                        numTransaction = sum(value for key, value in wallet['dailyAllTransactions'].items() if key >= str(self.three_months_ago))
                        if 0<=numTransaction <= 5000:
                            wallet['numTransaction'] = numTransaction
                            if 'type' not in wallet:
                                wallet['type'] = 0
                            wallet_lst.append(wallet)
            if len(wallet_lst) !=0:
                jobs = chunk_list(
                    wallet_lst, 
                    chunk_size=self.wallets_per_job
                    )
                for job in jobs:
                    #self._export_users_available(wallet_lst= job, name=f'tracking_{self.name}')
                    self.exchange_service._generate_exchange_info(job)

    def _export_users_available(self, wallet_lst,name):
        self.exporter.update_data(name=name, data=wallet_lst)
    def _end(self):
        self.batch_executor.shutdown()


    