import os
import requests
import pandas as pd 
from multithread_processing.base_job import BaseJob
import json
import time
def format_prices(prices):
    formatted_prices = {}
    for price in prices:
        timestamp = price[0]
        price_value = price[1]
        formatted_prices[timestamp] = price_value
    return formatted_prices

def get_historical_prices(token_id, days=60, vs_currency='usd'):
    url = f'https://api.coingecko.com/api/v3/coins/{token_id}/market_chart?vs_currency={vs_currency}&days={days}'
    response = requests.get(url)
    if response.status_code == 200:
        time.sleep(6)
    elif response.status_code == 429:
        time.sleep(70)
        response = requests.get(url)
        if  response.status_code == 429:
            time.sleep(60)
            response = requests.get(url)
            if response.status_code == 429:
                time.sleep(60)
        
    else:
        return None
    data = response.json()
    prices = data.get('prices', [])
    formatted_prices = format_prices(prices)
    prices_dict = {token_id: formatted_prices}
    return prices_dict
    
class GetTokenPrice(BaseJob):
    def __init__(self, exporter, name, token_addresses: list,
                 max_workers= 4, batch_size=500):
        self.token_history = dict()
        self.exporter = exporter
        self.name = name
        super().__init__(work_iterable=token_addresses,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        history_lst = []
        for smart_contract in works:
            idCoin = smart_contract['idCoingecko']
            address = smart_contract['address']
            id = smart_contract['_id']
            historical_token_price = get_historical_prices(idCoin)
            if (historical_token_price[idCoin] != {}):
                historical_token_round_price = dict()
                historical_token_round_price['_id'] = id
                historical_token_round_price['address'] = address
                historical_token_round_price['priceHistory'] = {str(timestamp - (timestamp % 86400000)): value for timestamp, value in historical_token_price[f'{idCoin}'].items()}
                history_lst.append(historical_token_round_price)
            else:
                if not os.path.exists(f'data/log_file/failed_tokens'):
                    try:
                        os.makedirs(f'data/log_file/failed_tokens')
                    except Exception as ex:
                        with open(f'data/log_file/failed_tokens/failed_tokens.json', 'a') as f:
                            f.write(json.dumps(smart_contract['address']))
                            f.write("\n")
                        
                with open(f'data/log_file/failed_tokens/failed_tokens.json', 'a') as f:
                            f.write(json.dumps(smart_contract['address']))
                            f.write("\n")
        if len(history_lst)>0:
            print(history_lst)
            self.exporter.update_data(name=self.name, data=history_lst)


    def _end(self):
        super()._end()
