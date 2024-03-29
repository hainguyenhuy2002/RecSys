import json
import os
import pandas as pd
from multithread_processing.base_job import BaseJob
from utils.ethereum_utils import filter_out_contracts


class checkAddressContractService(BaseJob):
    def __init__(self, chain_id, saving_path, lst_addresses, max_workers= 4, batch_size=500):
        self.is_contract = dict()
        self.chain_id = chain_id
        self.saving_path = saving_path
        super().__init__(work_iterable=lst_addresses,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        try:     
            is_contract = filter_out_contracts(works, chain_id=self.chain_id)
            self.is_contract.update(is_contract)


        except Exception as e:
            print(e)
            for work in works:
                if not os.path.exists(f'data/log_file/is_contract/'):
                    os.makedirs(f'data/log_file/is_contract/')
                with open(f'data/log_file/is_contract/failed_addresses.json', 'a') as f:
                    f.write(json.dumps(work))
                    f.write("\n")
                with open(f'data/log_file/is_contract/fail_problem.json', 'a') as f:
                    f.write(json.dumps(e))
                    f.write("\n")
                pass
        
    def _end(self):
        super()._end()        

        with open(f'{self.saving_path}/is_contract_address.json', 'w') as wfile:
            json.dump(self.is_contract, wfile, indent=4)

        