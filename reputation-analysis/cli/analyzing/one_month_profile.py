
import click
import pandas as pd 
from utils.logger_utils import get_logger
from services.one_month_profile_service import GetWalletInfo
from constants.time_constants import TimeConstants
from databases.mongodb_entity import MongoDBEntity
from constants.network_constants import Chains


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--chain', default='bsc', show_default=True, type=str,
              help='Network name example bsc or polygon')

@click.option('-i', '--input_path', type=str,
              help='Path to input addresses')
@click.option('-sv', '--saving_path', type=str,
              help='Path to save time_amount file')
@click.option('-b', '--batch-size', type=int, default=TimeConstants.AN_HOUR, show_default=True,
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def one_month_profile(chain, input_path, saving_path, batch_size, max_workers):
    logger = get_logger('User infromation exporter')
    chain_id = Chains.mapping[chain]
    logger.info("Start to connect MongoDB KLG")
    try:
        mongo_klg = MongoDBEntity()
        mongo_klg_wallet=mongo_klg.wallets
        logger.info("Successful connect to MongoDB")

    except Exception as e:
        logger.info(e)

    input_df = pd.read_json(input_path)
    input_address = input_df.wallet.unique().tolist()
    addresses = []
    for address in input_address:
        addresses.append(f'{chain_id}_'+str(address))

    job = GetWalletInfo(mongo_klg_wallet=mongo_klg_wallet,
                             wallets_list= addresses, 
                             reputation_df= input_df,
                             filename=saving_path, 
                             max_workers=batch_size, 
                             batch_size=max_workers)
    job.run()
