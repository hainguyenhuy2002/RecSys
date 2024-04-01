import os
import click
import requests
import json
import pandas as pd 
from databases.mongodb import MongoDB
from databases.mongodb_entity import MongoDBEntity
from services.generate_user_item_data_service import GetUserItem

@click.command(context_settings=dict(help_option_names=['-h', '--help']))

@click.option('-a', '--aave_path', type=str, default='', show_default=True,
              help='Path to input addresses')
@click.option('-sv', '--saving_path', type=str,
              help='name')
@click.option('-t', '--time_stamp', type=int, default=1711421985)
@click.option('-b', '--batch_size', type=int)
@click.option('-w', '--max_workers', default=8, show_default=True, type=int,
              help='The number of workers')

def generate_user_item_data(aave_path, saving_path, time_stamp, batch_size, max_workers):
    with open(aave_path,'r') as file:
        aave_address = json.load(file)
    mongo_clt = MongoDB()
    mongo_klg = MongoDBEntity()

    lenn = len(aave_address[0:100])
    index_list = list(range(batch_size, lenn, batch_size))
    index_list.append(lenn)

    job =GetUserItem(mongo_klg=mongo_klg, mongo_clt=mongo_clt, index_lst=index_list, aave_addresses= aave_address[0:100], saving_path= saving_path, timestamp=time_stamp,
                            max_workers=max_workers, batch_size=batch_size)
    
    job.run()
