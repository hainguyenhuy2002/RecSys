import click
import requests
import pandas as pd 
from utils.logger_utils import get_logger
from services.profiling_service import GetTransactionInfo
from constants.network_constants import Chains
from constants.time_constants import TimeConstants
from databases.mongodb_main import MongoDBMain


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--chain', default='bsc', show_default=True, type=str,
              help='Network name example bsc or polygon')
@click.option('-d', '--direction', default='sneding', show_default=True, type=str,
              help='direction of transaction of an wallet (sending or receiving)')
@click.option('-i', '--input_path', type=str,
              help='Path to input addresses')
@click.option('-sv', '--saving_path', type=str,
              help='Path to save time_amount file')
@click.option('-s', '--start', type=int,
              help='starting time to query')
@click.option('-e', '--end', type=int,
              help='ending time to query')
@click.option('-b', '--batch-size', type=int, default=TimeConstants.AN_HOUR, show_default=True,
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def profiling(chain, direction, input_path, saving_path, start, end, batch_size, max_workers):
        
    logger = get_logger('User infromation exporter')

    input_df = pd.read_json(input_path)
    addresses = input_df.wallet.unique().tolist()
    historical_token_price = get_historical_prices('ethereum')
    historical_token_round_price = dict()
    historical_token_round_price['ethereum'] = {(timestamp - (timestamp % 86400000)): value for timestamp, value in historical_token_price['ethereum'].items()}



    job = GetTransactionInfo(chain=chain, 
                             collections='transactions', 
                             historical_token_price=historical_token_round_price,
                             wallets_list= addresses, 
                             reputation_df= input_df,
                             direction=direction,
                             filename=saving_path, 
                             start_date=start, 
                             end_date= end, 
                             max_workers=batch_size, 
                             batch_size=max_workers)
    job.run()


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
        data = response.json()
        prices = data.get('prices', [])
        formatted_prices = format_prices(prices)
        prices_dict = {token_id: formatted_prices}
        return prices_dict
    else:
        return None