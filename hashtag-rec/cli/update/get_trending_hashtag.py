import click
import json
import json
import re
import pandas as pd
import textdistance as td
from keybert import KeyBERT
from collections import Counter
from keyphrase_vectorizers import KeyphraseCountVectorizer
from constant.twitter_constant import Dapps
from utils.logger_utils import get_logger
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
    #pretrain model
    kw_model = KeyBERT(model='all-mpnet-base-v2')

    
    pass