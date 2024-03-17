import json
import os
from pymongo import MongoClient
from typing import Dict, Set, List
from multithread_processing.base_job import BaseJob
from utils.logger_utils import get_logger

class GetAddress(BaseJob):
    def __init__(self, importer, arangoDb, exporter, name,flagged_lst: list, max_workers= 4, batch_size=500):
        self.mongo_klg = importer
        self.exporter = exporter
   #     self.arangoDb = arangoDb
       # self.arango = arangodb
        self.name = name
        super().__init__(work_iterable=flagged_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        for work in works:
            wallet_lst: List[Dict] = list()
            try:
                query =  {"flagged":work, "chainId":"0x1", "balanceChangeLogs":{"$exists":"True"},"type":"wallet", "balanceInUSD":{"$lte":50000}, "balanceInUSD":{"$gte":10}}
                wallets = self.mongo_klg.find(query,{'_id':1,'flagged':1,'balanceChangeLogs':1,'address':1})
                for wallet in wallets:
                #  wallet_sent_receive = self.arangoDb.get_num_send_receive(wallet['address'])
                # if (wallet_sent_receive['numberSent'] >300) |((wallet_sent_receive['numberReceived'] >300)):
                #     continue
                # else: 
                    wallet_lst.append({
                                '_id':wallet['_id'],
                                'address': wallet['address'],
                                'flagged': wallet['flagged'],
                                'balanceChangeLogs': wallet['balanceChangeLogs'],
                            })
                if len(wallet_lst) !=0:
                    self._export_users_available(wallet_lst= wallet_lst, name=self.name)
            except Exception as e:
                get_logger(e)
                continue
    def _export_users_available(self, wallet_lst,name):
        #self.exporter._db[f"{name}"].bulk_write(wallet_lst)
        self.exporter.update_data(name=name, data=wallet_lst)
    def _end(self):
        self.batch_executor.shutdown()


    