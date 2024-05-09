import requests
import time
def format_prices(prices):
    formatted_prices = {}
    for price in prices:
        timestamp = price[0]
        price_value = price[1]
        formatted_prices[timestamp] = price_value
    return formatted_prices

def get_historical_prices(token_id, days=10, vs_currency='usd'):
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