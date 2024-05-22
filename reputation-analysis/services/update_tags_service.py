import json
import os
from databases.mongodb import MongoDB
from multithread_processing.base_job import BaseJob
from utils.ethereum_utils import filter_out_contracts


class UpdateTagsServices(BaseJob):
    def __init__(self,  address_lst, max_workers= 4, batch_size=1000):
        self.is_contract = dict()
        super().__init__(work_iterable=address_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        cursor =
        
    def _end(self):
        super()._end()        

        with open(f'{self.saving_path}/is_contract_address.json', 'w') as wfile:
            json.dump(self.is_contract, wfile, indent=4)

        