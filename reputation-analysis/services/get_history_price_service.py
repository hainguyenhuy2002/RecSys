import os
import pandas as pd 
from multithread_processing.base_job import BaseJob
from utils.history_price_utils import get_historical_prices
from utils.logger_utils import write_file

class GetTokenPrice(BaseJob):
    def __init__(self, exporter, chain_id, name, token_addresses: list,
                 max_workers= 2, batch_size=2):
        self.token_history = dict()
        self.exporter = exporter
        self.name = name
        self.chain_id = chain_id
        super().__init__(work_iterable=token_addresses,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        history_lst = []
        for smart_contract in works:
            try:
                idCoin = smart_contract['idCoingecko']
                address = smart_contract['address']
                id = smart_contract['_id']
                historical_token_price = get_historical_prices(idCoin)
                if (historical_token_price[idCoin] != {}):
                    historical_token_round_price = dict()
                    historical_token_round_price['_id'] = id
                    historical_token_round_price['chainId'] = self.chain_id
                    historical_token_round_price['address'] = address
                    historical_token_round_price['idCoingecko'] = idCoin
                    historical_token_round_price['priceHistory'] = {str(timestamp - (timestamp % 86400000)): value for timestamp, value in historical_token_price[f'{idCoin}'].items()}
                    history_lst.append(historical_token_round_price)
                else:
                    write_file(
                            folder_direction='data/log_file/failed_tokens/failed_{self.chain_id}_tokens',
                            name='failed_tokens.json',
                            file=smart_contract['address']
                    )
        
            except Exception as e:
                write_file(
                            folder_direction='data/log_file/failed_tokens/failed_{self.chain_id}_tokens',
                            name='failed_tokens.json',
                            file=smart_contract['address']
                    )
                continue

        if len(history_lst)>0:
            self.exporter.update_docs(collection_name=self.name, data=history_lst, merge=True)    
    def _end(self):
        super()._end()
