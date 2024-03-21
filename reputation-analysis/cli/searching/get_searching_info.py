import os
import json
import click
import requests
import pandas as pd 
from typing import List
from dotenv import load_dotenv
from utils.logger_utils import get_logger
##from services.three_month_profile_service import GetWalletTransactionTransfer
from services.transaction_info_service import GetWalletTransactionTransfer
from constants.network_constants import Chains
from constants.time_constants import TimeConstants
from databases.mongodb_main import MongoDBMain
from databases.mongodb import MongoDB
from databases.postgresql import PostgresDB
from services.web3_service  import web3_service

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--chain', default='bsc', show_default=True, type=str,
              help='Network name example bsc or polygon')
# @click.option('-d', '--direction', default='sneding', show_default=True, type=str,
#               help='direction of transaction of an wallet (sending or receiving)')
@click.option('-ih', '--input_hot', type=str,
              help='Path to hot walelt addresses')
@click.option('-ib', '--input_mint_burn', type=str,
              help='Path to mint burn wallet addresses')
@click.option('-n', '--name', type=str,
              help='Path to save time_amount file')
@click.option('-s', '--start', type=int,
              help='starting time to query')
@click.option('-e', '--end', type=int,
              help='ending time to query')
@click.option('-sb', '--start_block', type=int, default=None, show_default=True,
              help='starting block to query')
@click.option('-eb', '--end_block', type=int, default=None, show_default=True,
              help='ending block to query')
@click.option('-tp', '--token_price', type=str,
              help='path to token price history')
@click.option('-so', '--sources', type=str, default=None, show_default=True,
              help='ending block to query')
@click.option('-b', '--batch-size', type=int, default=TimeConstants.AN_HOUR, show_default=True,
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def get_searching_info(chain, input_hot, input_mint_burn, name, start, end, start_block, end_block, token_price, sources, batch_size, max_workers):
    logger = get_logger('User infromation exporter')
    if (start_block == None) | (end_block ==None):
        logger.info("Start map timestamp to block number")
        load_dotenv()
        INFURA_URL = os.getenv("INFURA_API")
        web3 = web3_service(infura_url=INFURA_URL)
        #Get block from timestamp
        try: 
            start_block = web3._get_block_from_timestamp(start)
            end_block = web3._get_block_from_timestamp(end)
            logger.info(f"Successful map timestamp to block number with starting block: {start_block} and ending block: {end_block}")
        except Exception as e:
            logger.info(e)

    logger.info("Start to connect MongoDB and PostgresDB Database")
    try:
        mongo = MongoDBMain(chain=chain)
        chain_id = Chains.mapping[chain]

        postgres = PostgresDB()
        mongo_clustering = MongoDB()
        mongo_available_addresses = mongo_clustering._db['searching_addresses_filter_type']
        logger.info("Successful connect to MongoDB and PosgresDB")

    except Exception as e:
        logger.info(e)


    if token_price == None:
        logger.info("Start to get the mapping token history prices dictionary")
        try:
            historical_token_price = get_historical_prices('ethereum')
            historical_token_round_price = dict()
            historical_token_round_price['ethereum'] = {(timestamp - (timestamp % 86400000)): value for timestamp, value in historical_token_price['ethereum'].items()}
            logger.info("Sucessful get mapping timestamp dictionary and the mapping token history")           

        except Exception as e:
            logger.info(e)

    else:
        with open(token_price, 'r') as  token_file:
            historical_token_round_price  = json.load(token_file)
    

    logger.info("Start to get the mapping timestamp dictonary")
    block_timestamp_mappings = mongo.get_block_number_to_timestamp(start_block=start_block, end_block=end_block)
    logger.info("Sucessful mapping timestamp dictionary")           
    # with open('data/block_timestamp_mapping.json','w') as jfile:
    #     json.dump(block_timestamp_mappings, jfile, indent=4)
    # with open('data/block_timestamp_mapping.json','r') as jfile:
    #     block_timestamp_mappings = json.load(jfile)

    with open(input_hot, 'r') as file:
        hot_wallets = json.load(file)
    hot_wallets_lst = []
    for exchange, data in hot_wallets.items():
        if "0x1" in data["wallets"]:
            hot_wallets_lst.extend(data["wallets"]["0x1"])

    with open(input_mint_burn, 'r') as file:
        mint_burn = json.load(file)

    mint_burn_lst = mint_burn[f'{chain_id}']    
    hot_wallets_lst.extend(mint_burn_lst)


    cursor = mongo_available_addresses.find()
    addresses = []
    for address in cursor[0:100]:
        if (address['numberReceived']<= 150) &(address['numberSent']<=150) &(address['address'] not in hot_wallets_lst) &(address['type']!='contract'):
            addresses.append(address['address'])
    
    #addresses = ['0xc0f310084e7c63c12e49e056a33a3176354a8e53']

    if sources != None:
        sources = [sources]
        print(sources)
    job = GetWalletTransactionTransfer(chain=chain, 
                             mongo_transaction= mongo,
                             postgres= postgres,
                             exporter=mongo_clustering,
                             historical_token_price=historical_token_round_price,
                             block_timestamp_mappings=block_timestamp_mappings,
                             special_wallets= hot_wallets_lst,
                             wallets_list= addresses, 
                 #            direction=direction,
                             filename=name, 
                             start_date=start, 
                             end_date= end, 
                             start_block=start_block,
                             end_block=end_block,
                             max_workers=batch_size, 
                             batch_size=max_workers,
                             sources=sources)
    job.run()


def format_prices(prices):
    formatted_prices = {}
    for price in prices:
        timestamp = price[0]
        price_value = price[1]
        formatted_prices[timestamp] = price_value
    return formatted_prices

def get_historical_prices(token_id, days=95, vs_currency='usd'):
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