import click
import json
import pandas as pd

from utils.logger_utils import get_logger
from constants.network_constants import Chains
from databases.mongodb_entity import MongoDBEntity
from services.get_history_price_service import GetTokenPrice     
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-i', '--input_path', type=str,
              help='Path to input addresses')
@click.option('-sv', '--saving_path', type=str,
              help='Path to save time_amount file')
@click.option('-b', '--batch-size', type=int, 
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def get_token_price(input_path, saving_path, batch_size, max_workers):
    with open(input_path, "r") as json_file:
        token_list = json.load(json_file)

    logger=get_logger("Start to get tokens history")

    job = GetTokenPrice(token_addresses=token_list, filename=saving_path,batch_size=batch_size,max_workers=max_workers)
    job.run()
