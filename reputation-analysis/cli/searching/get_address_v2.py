import click
import json

from services.get_address_service import GetAddress
from services.transaction_info_service_v2 import GetTransactionInfoService
from databases.mongodb_entity import MongoDBEntity
from databases.mongodb import MongoDB
from databases.mongodb_main import MongoDBMain
from databases.postgresql import PostgresDB
from constants.network_constants import Chains
from utils.list_dict_utils import get_special_wallet_list

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-n', '--name', type=str,
              help='Folder path to save training data file')
@click.option('-h', '--hot_path', type=str,
              help='input of hot wallet')
@click.option('-bm', '--burn_mint_path', type=str,
              help='input of hot wallet')
@click.option('-tp', '--token_price', type=str,
              help='collection to store token price')
@click.option('-b', '--batch-size', type=int, default=1, show_default=True,
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')
def get_address(name, hot_path, burn_mint_path, token_price, batch_size, max_workers):
    ## get special wallet list

    special_wallet_lst = get_special_wallet_list(hot_path=hot_path, 
                                             burn_mint_path=burn_mint_path)
    
    token_price = mongo_community._db[f'{token_price}'].find()
    historical_token_round_price = dict()
    for token in token_price:
        token_dct = dict()
        address = token['address']
        price_history = token['priceHistory']
        token_dct[f'{address}'] = price_history
        historical_token_round_price.update(token_dct)


    chain_names = Chains.all_name
    mongo_transaction = MongoDBMain(chain=chain)
    postgres = PostgresDB()


    mongo_klg = MongoDBEntity()
    mongo_klg_wallets = mongo_klg.wallets
    mongo_community = MongoDB()






    flagged_lst = [i for i in range(1,5000)]
    
    exchange_service = GetTransactionInfoService(
                             mongo_transaction=mongo_transaction,
                             postgres=postgres,
                             mongo_community=mongo_community,
                             historical_token_price=historical_token_round_price,
                             block_timestamp_mappings=block_timestamp_mappings,
                             special_wallets=special_wallet_lst,
                             index_lst=index_list,

                             filename=name, 
                             start_date=start, 
                             end_date= end, 
                             start_block=start_block,
                             end_block=end_block,
                             max_workers=max_workers, 
                             batch_size=batch_size)


    job = GetAddress(importer=mongo_klg_wallets,
                     exporter=mongo_community,
                     hot_wallets=hot_wallets_lst,
                     name=name,
                     flagged_lst=flagged_lst, 
                     max_workers=max_workers, 
                     batch_size=batch_size)
    job.run()
