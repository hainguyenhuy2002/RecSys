import click
import json
import pandas as pd
from cli_scheduler.scheduler_job import SchedulerJob

from utils.logger_utils import get_logger
from constants.network_constants import Chains
from constants.time_constants import TimeConstants
from databases.mongodb_entity import MongoDBEntity
from databases.mongodb import MongoDB
from services.get_history_price_service import GetTokenPrice     


logger = get_logger('Get token price Scheduler')


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--chain', type=str,
              help='chain to get token price')
@click.option('-n', '--name', type=str,
              help='name of collection')
@click.option('-f', '--failed', type=str, default=None, show_default=True,
              help='Is token has failed addresses?')
@click.option('-b', '--batch-size', type=int, 
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

@click.option('--interval', default=TimeConstants.DAYS_7, show_default=True, type=int,
              help='Interval to repeat the job')
@click.option('--delay', default=0, show_default=True, type=int, help='Time (in seconds) to delay')
@click.option('--run-now', default=True, show_default=True, type=bool,
              help='False to wait until interval then run')

def get_token_price(chain, name, failed, batch_size, max_workers, interval, delay, run_now):
    chain_id = Chains.mapping[chain]
    mongo_klg = MongoDBEntity()
    mongo_db = MongoDB()
    if failed == None:
        cursor =mongo_klg._db['smart_contracts'].find({"chainId": chain_id, "idCoingecko":{"$exists":True},  "price":{"$gt":0}, "marketCap":{"$gt":1000000}})
        columns = ['_id','address','idCoingecko']
        token_list = []
        for c in cursor:
            token_list.append({key: c.get(key) for key in columns})
    else:
        try:
            tokens = []
            with open(f'data/log_file/failed_tokens/failed_{chain_id}_tokens/failed_tokens.json') as file:
                for failed_token in file:
                    failed_addresses = json.loads(failed_token)
                    tokens.append(failed_addresses)
        except Exception as e:
            logger.info(e)
            logger.info(f"{chain} does not have failed top tokens addresses")
            return

        token_list = []
        for token in tokens:
            token_info_dct = dict()
            token_info = list(mongo_klg._db['smart_contracts'].find({'_id':f'{chain_id}_{token}'}))[0]
            token_info_dct['_id'] = token_info['_id']
            token_info_dct['address'] = token_info['address']
            token_info_dct['idCoingecko'] = token_info['idCoingecko']
            token_list.append(token_info_dct)
    
    job = GetTokenPriceSchedulerJob(
        interval=interval,
        delay=delay,
        run_now=run_now,
        mongodb=mongo_db, 
        name=name, 
        chain_id=chain_id, 
        token_list=token_list,
        batch_size=batch_size,
        max_workers=max_workers)
    job.run()


class GetTokenPriceSchedulerJob(SchedulerJob):
    def __init__(self,
                 # scheduler job
                 interval,
                 delay,
                 run_now,
                 # loader job
                 mongodb,
                 name,
                 chain_id,
                 token_list,
                 batch_size,
                 max_workers,
                 ):
        self.chain_id = chain_id
        scheduler = f"^{run_now}@{interval}/{delay}#true"
        super().__init__(scheduler)

        self.mongodb = mongodb
        self.name = name
        self.chain_id = chain_id
        self.token_list = token_list
        self.batch_size = batch_size
        self.max_workers = max_workers

    def _execute(self, *args, **kwargs):
        job = GetTokenPrice(exporter=self.mongodb, 
                            name=self.name, 
                            chain_id=self.chain_id, 
                            token_addresses=self.token_list,
                            batch_size=self.batch_size,
                            max_workers=self.max_workers)
        job.run()




