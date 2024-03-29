import click
import json
from utils.logger_utils import get_logger
from constants.network_constants import Chains
from services.check_address_contract_service import checkAddressContractService     
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--chain', default='bsc', show_default=True, type=str,
              help='Network name example bsc or polygon')
@click.option('-i', '--input_path', type=str,
              help='Path to input addresses')
@click.option('-sv', '--saving_path', type=str,
              help='Path to save time_amount file')
@click.option('-b', '--batch_size', type=int, 
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max_workers', default=8, show_default=True, type=int,
              help='The number of workers')

def check_address_contract(chain, input_path, saving_path, batch_size, max_workers):
    logger = get_logger('Start to check contract')
    chain_id = Chains.mapping[chain]
    with open(input_path,'r') as file:
        top_addresses = json.load(file)
    job = checkAddressContractService(chain_id=chain_id, saving_path=saving_path, lst_addresses=top_addresses,
                                      batch_size=batch_size, max_workers=max_workers)
    job.run()
