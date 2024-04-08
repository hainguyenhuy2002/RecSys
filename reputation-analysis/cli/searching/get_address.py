import click
import json
from services.get_address_service import GetAddress
from databases.mongodb_entity import MongoDBEntity
from databases.mongodb import MongoDB
from databases.arangodb_klg import ArangoDB
from constants.network_constants import Chains
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--chain', type=str,
              help='chain name')
@click.option('-n', '--name', type=str,
              help='Folder path to save training data file')
@click.option('-h', '--hot_path', type=str,
              help='input of hot wallet')
@click.option('-bm', '--burn_mint_path', type=str,
              help='input of hot wallet')
@click.option('-b', '--batch-size', type=int, default=1, show_default=True,
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')
def get_address(chain, name, hot_path, burn_mint_path, batch_size, max_workers):
    
    chain_id = Chains.mapping[chain]
    with open(hot_path, 'r') as file:
        hot_wallets = json.load(file)
    hot_wallets_lst = []
    for exchange, data in hot_wallets.items():
        if "0x1" in data["wallets"]:
            hot_wallets_lst.extend(data["wallets"]["0x1"])

    with open(burn_mint_path, 'r') as file:
        mint_burn = json.load(file)

    mint_burn_lst = mint_burn[f'{chain_id}']    
    hot_wallets_lst.extend(mint_burn_lst)
    mongoKlg = MongoDBEntity()
    mongoKlg_wallets = mongoKlg.wallets
    mongoSubgraph = MongoDB()
    arangoDb = ArangoDB()
    flagged_lst = [i for i in range(1,3945)]
    job = GetAddress(importer=mongoKlg_wallets,
                     arangoDb= arangoDb,
                     exporter=mongoSubgraph,
                     hot_wallets=hot_wallets_lst,
                     chain_id=chain_id,
                     name=name,
                     flagged_lst=flagged_lst, 
                     max_workers=max_workers, 
                     batch_size=batch_size)
    job.run()
