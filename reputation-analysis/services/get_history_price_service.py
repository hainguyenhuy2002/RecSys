import requests
import pandas as pd 
from multithread_processing.base_job import BaseJob
import json
import requests
import time
def format_prices(prices):
    formatted_prices = {}
    for price in prices:
        timestamp = price[0]
        price_value = price[1]
        formatted_prices[timestamp] = price_value
    return formatted_prices

def get_historical_prices(token_id, days=92, vs_currency='usd'):
    url = f'https://api.coingecko.com/api/v3/coins/{token_id}/market_chart?vs_currency={vs_currency}&days={days}'
    response = requests.get(url)
    print(response.status_code)
    if response.status_code == 200:
        time.sleep(3)
    elif response.status_code == 429:
        time.sleep(60)
        response = requests.get(url)
    else:
        return None
    data = response.json()
    prices = data.get('prices', [])
    formatted_prices = format_prices(prices)
    prices_dict = {token_id: formatted_prices}
    return prices_dict
    
class GetTokenPrice(BaseJob):
    def __init__(self, mongo_klg_contract, token_addresses: list,filename,
                 max_workers= 4, batch_size=500):
        self.mongo_klg_contract = mongo_klg_contract
        self.token_history = dict()
        self.filename = filename

        super().__init__(work_iterable=token_addresses,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        smart_contracts = self.mongo_klg_contract.find({'_id': {'$in': works},'idCoingecko':{"$exists": True}},{'_id':1,'idCoingecko':1,'address':1})
        for smart_contract in smart_contracts:
            idCoin = smart_contract['idCoingecko']
            address = smart_contract['address']
            historical_token_price = get_historical_prices(idCoin)
            if historical_token_price == None:
                continue
            historical_token_round_price = dict()
            historical_token_round_price[f'{address}'] = {(timestamp - (timestamp % 86400000)): value for timestamp, value in historical_token_price[f'{idCoin}'].items()}
 
            self.token_history.update(historical_token_round_price)


    def _end(self):
        super()._end()
        with open(f'{self.filename}/aave_tokens.json', "w") as json_file:
            json.dump(self.token_history, json_file, indent=4)