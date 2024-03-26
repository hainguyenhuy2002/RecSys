import os
import click
import requests
import json
import pandas as pd 
from databases.mongodb import MongoDB
from services.generate_training_data_service import GenerateData

@click.command(context_settings=dict(help_option_names=['-h', '--help']))

@click.option('-a', '--aave_path', type=str,
              help='Path to input addresses')
@click.option('-n', '--name', type=str,
              help='name')
@click.option('-d', '--direction', type=str,
              help='train or search')
@click.option('-t', '--time-stamp', type=int, default=1711421985)
@click.option('-b', '--batch-size', type=int)
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def generate_training_data(aave_path, name, direction, time_stamp, batch_size, max_workers):
    with open(aave_path,'r') as file:
        aave_address = json.load(file)
    mongodb = MongoDB()
    mongo_searching_18_3 = mongodb._db['addresses_searching_18_3']
    num_documents = mongo_searching_18_3.estimated_document_count()
    lenn = len(aave_address)
    if direction == 'train':
        index_list = list(range(batch_size, lenn, batch_size))
        index_list.append(num_documents)
    elif direction =='search':
        index_list = list(range(batch_size, num_documents-lenn, batch_size))
        index_list.append(num_documents)
    job =GenerateData(importer=mongo_searching_18_3, exporter= mongodb, name=name, direction=direction, index_lst=index_list,aave_addresses= aave_address, timestamp=time_stamp,
                            max_workers=max_workers, batch_size=batch_size)
    
    job.run()
