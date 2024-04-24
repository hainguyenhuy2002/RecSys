import os
import click
import requests
import json
import pandas as pd 
from databases.mongodb import MongoDB
from services.get_reputation_score_service import GetReputationScore

@click.command(context_settings=dict(help_option_names=['-h', '--help']))

@click.option('-a', '--aave_path', type=str, default='', show_default=True,
              help='Path to input addresses')
@click.option('-sv', '--saving_path', type=str,
              help='saving_path')
@click.option('-t', '--time_stamp', type=int, default=1711421985)
@click.option('-b', '--batch-size', type=int)
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def get_reputation_score(aave_path, saving_path, time_stamp, batch_size, max_workers):
    with open(aave_path,'r') as file:
        aave_address = json.load(file)
    mongodb = MongoDB()
    mongo_searching_18_3 = mongodb._db['addresses_searching_18_3']
    lenn = len(aave_address)
    index_list = list(range(batch_size, lenn, batch_size))
    index_list.append(lenn)

    job =GetReputationScore(importer=mongo_searching_18_3, saving_path=saving_path, lst_addresses= index_list, aave_address= aave_address, timestamp=time_stamp, max_workers=max_workers, batch_size=batch_size)
    
    job.run()
