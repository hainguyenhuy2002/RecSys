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
@click.option('-f', '--failed', type=str, default=None, show_default=True,
              help='Is token has failed addresses?')
@click.option('-b', '--batch-size', type=int, 
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def get_token_price(chain, name, failed, batch_size, max_workers):
    logger = get_logger("Start to get tokens history")
    chain_id = Chains.mapping[chain]
    mongo_klg = MongoDBEntity()
    mongo_db = MongoDB()
    if failed == None:
        token_addresses = list(mongo_klg._db['configs'].find({'_id':f'top_tokens_{chain_id}'}))
        tokens = []
        for tok  in token_addresses[0]['tokens']:
            tokens.append(tok['address'])
    else:
        try:
            tokens = []
            with open(f'data/log_file/failed_tokens/failed_{chain_id}_tokens/failed_tokens.json') as file:
                for failed_token in file:
                    failed_addresses = json.loads(failed_token)
                    tokens.append(failed_addresses)
        except Exception as e:
            logger.info(e)
            logger.info(f"{chain} does not have failed top tokens addresses")
            return

        

    token_list = []
    for token in tokens:
        token_info_dct = dict()
        token_info = list(mongo_klg._db['smart_contracts'].find({'_id':f'{chain_id}_{token}'}))[0]
        token_info_dct['_id'] = token_info['_id']
        token_info_dct['address'] = token_info['address']
        token_info_dct['idCoingecko'] = token_info['idCoingecko']
        token_list.append(token_info_dct)
    print(token_list)
    job = GetTokenPrice(exporter=mongo_db, name=name, chain_id=chain_id, token_addresses=token_list,batch_size=batch_size,max_workers=max_workers)





    job.run()
