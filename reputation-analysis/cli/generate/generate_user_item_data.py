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
@click.option('-c', '--contract_path', type=str, default='', show_default=True,
              help='Path to input contract addresses')
@click.option('-d', '--direction', type=str,
              help='lendings or contracts')
@click.option('-sv', '--saving_path', type=str,
              help='name')
@click.option('-t', '--time_stamp', type=int, default=1711421985)
@click.option('-b', '--batch_size', type=int)
@click.option('-w', '--max_workers', default=8, show_default=True, type=int,
              help='The number of workers')

def generate_user_item_data(aave_path, contract_path, direction, saving_path, time_stamp, batch_size, max_workers):
    with open(aave_path,'r') as file:
        aave_address = json.load(file)
    with open(contract_path, 'r') as rfile:
        contract_address = json.load(rfile)

    mongo_clt = MongoDB()
    mongo_klg = MongoDBEntity()
    num_documents = MongoDB()._db['addresses_searching_18_3'].estimated_document_count()
    if direction == 'lendings':
        job =GetUserItem(mongo_klg=mongo_klg, mongo_clt=mongo_clt,index_lst=aave_address, contract_set= set(contract_address),saving_path= saving_path, direction=direction, timestamp=time_stamp,
                            max_workers=max_workers, batch_size=batch_size)
    elif direction =='contracts':
        index_list = list(range(batch_size, num_documents, batch_size))
        index_list.append(num_documents)
        job =GetUserItem(mongo_klg=mongo_klg, mongo_clt=mongo_clt,index_lst=index_list, contract_set= set(contract_address),saving_path= saving_path, direction=direction, timestamp=time_stamp,
                                max_workers=max_workers, batch_size=batch_size)
    
    job.run()
