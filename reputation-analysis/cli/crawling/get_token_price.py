import click
import json
import pandas as pd

from utils.logger_utils import get_logger
from constants.network_constants import Chains
from databases.mongodb_entity import MongoDBEntity
from databases.mongodb import MongoDB
from services.get_history_price_service import GetTokenPrice     
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--chain', type=str,
              help='chain to get token price')
@click.option('-n', '--name', type=str,
              help='name of collection')
@click.option('-b', '--batch-size', type=int, 
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def get_token_price(chain, name, batch_size, max_workers):
    chain_id = Chains.mapping[chain]
    mongo_klg = MongoDBEntity()
    mongo_db = MongoDB()
    token_addresses = list(mongo_klg._db['configs'].find({'_id':f'top_tokens_{chain_id}'}))
    token_list = []
    for token in token_addresses[0]['tokens']:
        token_info_dct = dict()
        address = token['address']
        token_info = list(mongo_klg._db['smart_contracts'].find({'_id':f'{chain_id}_{address}'}))[0]
        token_info_dct['_id'] = token_info['_id']
        token_info_dct['address'] = token_info['address']
        token_info_dct['idCoingecko'] = token_info['idCoingecko']
        token_list.append(token_info_dct)
    logger = get_logger("Start to get tokens history")

    job = GetTokenPrice(exporter=mongo_db, name=name, token_addresses=token_list,batch_size=batch_size,max_workers=max_workers)
    job.run()
