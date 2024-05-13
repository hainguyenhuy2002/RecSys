import requests
import time

from utils.list_dict_utils import update_dict_of_dict
from utils.logger_utils import get_logger

def format_prices(prices):
    formatted_prices = {}
    for price in prices:
        timestamp = price[0]
        price_value = price[1]
        formatted_prices[timestamp] = price_value
    return formatted_prices

def get_historical_prices(token_id, days=90, vs_currency='usd'):
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

def query_historical_prices(mongo_community, token_price, chains):
    logger = get_logger("Query token historical price job")
    try:
        token_price = mongo_community._db[f'{token_price}'].find()
        historical_token_price = dict()

        for chain_id in chains:
                historical_token_price[f'{chain_id}'] = {}

        for token in token_price:
            token_info =dict()
            token_dct = dict()
            address = token['address']
            price_history = token['priceHistory']
            chain_id = token['chainId']
            token_dct[f'{address}'] = price_history
            token_info[f'{chain_id}'] = token_dct

            historical_token_price = update_dict_of_dict(historical_token_price, token_info)
        logger.info("Done!!!")

    except Exception as e:
        logger.info("Error in query token historical price job")
        logger.info(e)
    return historical_token_price