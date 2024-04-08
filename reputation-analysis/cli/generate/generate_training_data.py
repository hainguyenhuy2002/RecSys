import os
import click
import requests
import json
import pandas as pd 
from databases.mongodb import MongoDB
from services.generate_training_data_service import GenerateData

@click.command(context_settings=dict(help_option_names=['-h', '--help']))

@click.option('-a', '--address_dapps', type=str, default='', show_default=True,
              help='Dapps users addresses')
@click.option('-s', '--address_searching', type=str, default='', show_default=True,
              help='address searching mongoDb')
@click.option('-n', '--name', type=str,
              help='name')
@click.option('-d', '--direction', type=str,
              help='train or search')
@click.option('-t', '--time-stamp', type=int, default=1711421985)
@click.option('-b', '--batch-size', type=int)
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def generate_training_data(address_dapps, address_searching, name, direction, time_stamp, batch_size, max_workers):

    mongodb = MongoDB()
    address_searching = mongodb._db[f'{address_searching}']
    num_documents = address_searching.estimated_document_count()
    if direction == 'train':
        with open(address_dapps,'r') as file:
            Dapps_user_address = json.load(file)
        index_list = list(range(batch_size, len(Dapps_user_address), batch_size))
        index_list.append(len(Dapps_user_address))
        job =GenerateData(importer=address_searching, exporter= mongodb, name=name, direction=direction, index_lst=index_list, Dapps_user_addresses= Dapps_user_address, timestamp=time_stamp,
                            max_workers=max_workers, batch_size=batch_size)
        job.run()

    elif direction =='search':
        index_list = list(range(batch_size, num_documents, batch_size))
        index_list.append(num_documents)
        job =GenerateData(importer=address_searching, exporter= mongodb, name=name, direction=direction, index_lst=index_list, timestamp=time_stamp, max_workers=max_workers, batch_size=batch_size)
        job.run()
    
