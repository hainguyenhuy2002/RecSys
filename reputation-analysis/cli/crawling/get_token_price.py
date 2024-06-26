import click
import json
import pandas as pd
import time

from cli_scheduler.scheduler_job import SchedulerJob
from utils.history_price_utils import get_daily_timestamp
from utils.logger_utils import get_logger
from constants.network_constants import Chains
from constants.time_constants import TimeConstants
from databases.mongodb_entity import MongoDBEntity
from databases.mongodb import MongoDB
from services.get_history_price_service import GetTokenPrice     


logger = get_logger('Get token price Scheduler')


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-c', '--chain', type=str, default=None, show_default=True,
              help='chain name')
@click.option('-n', '--name', type=str,
              help='name of collection')
@click.option('-f', '--failed', type=str, default=None, show_default=True,
              help='Is token has failed addresses?')
@click.option('-b', '--batch-size', type=int, 
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

@click.option('--interval', default=TimeConstants.A_DAY, show_default=True, type=int,
              help='Interval to repeat the job')
@click.option('--delay', default=0, show_default=True, type=int, help='Time (in seconds) to delay')
@click.option('--run-now', default=True, show_default=True, type=bool,
              help='False to wait until interval then run')

def get_token_price(chain, name, failed, batch_size, max_workers, interval, delay, run_now):
    mongodb = MongoDB()
    mongo_klg = MongoDBEntity()
    if chain!= None:
        chain_id = Chains.mapping[chain]
        logger.info(f"Get top token price in {chain_id}")
        job = CrawlTokenPriceSchedulerJob(
            interval=interval,
            delay=delay,
            run_now=run_now,
            failed=failed,
            mongodb=mongodb, 
            mongo_klg=mongo_klg,
            name=name, 
            chain_id=chain_id, 
            batch_size=batch_size,
            max_workers=max_workers)
        job.run()

    else:
        job=QueryTokenPriceSchedulerJob(
            interval=interval,
            delay=delay,
            run_now=run_now,
            mongodb=mongodb, 
            mongo_klg=mongo_klg,
            name=name, 
            batch_size=batch_size,
            max_workers=max_workers
        )
        job.run()


class QueryTokenPriceSchedulerJob(SchedulerJob):
    def __init__(self,
                    # scheduler job
                    interval,
                    delay,
                    run_now,
                    # loader job
                    mongo_klg,
                    mongodb,
                    name,
                    batch_size,
                    max_workers,
                    ):
            scheduler = f"^{run_now}@{interval}/{delay}#true"
            super().__init__(scheduler)
            self.mongodb = mongodb
            self.mongo_klg = mongo_klg
            self.name = name
            self.batch_size = batch_size
            self.max_workers = max_workers

    def _execute(self, *args, **kwargs):
        chains = Chains.alls
        logger.info(f"Get token price from chains: {chains}")
        for chain_id in chains:
            logger.info(f"Get top token price in {chain_id}")
            cursor =self.mongo_klg._db['smart_contracts'].find({"chainId": chain_id, "idCoingecko":{"$exists":True},  \
                                                                "price":{"$gt":0}, "marketCap":{"$gt":1000000}}) 
            token_list = []
            for c in cursor:
                idCoin = c['idCoingecko']
                address = c['address']
                id = c['_id']
                marketCap = c['marketCap']
                if 'priceChangeLogs' in c:
                    historical_token_price = c['priceChangeLogs']
                    if (historical_token_price!= {}):
                        if int(max(historical_token_price)) <(time.time() -TimeConstants.DAYS_3):
                            continue
                        else:
                            historical_token_round_price = dict()
                            historical_token_round_price['_id'] = id
                            historical_token_round_price['chainId'] = chain_id
                            historical_token_round_price['address'] = address
                            historical_token_round_price['idCoingecko'] = idCoin
                            historical_token_round_price['marketCap'] = marketCap
                            historical_token_round_price['priceHistory'] = {get_daily_timestamp(int(timestamp)*1000): value \
                                                                            for timestamp, value in historical_token_price.items()}
                            token_list.append(historical_token_round_price)
                    
            self.mongodb.update_docs(collection_name=self.name, data=token_list, merge=True)  






class CrawlTokenPriceSchedulerJob(SchedulerJob):
    def __init__(self,
                 # scheduler job
                 interval,
                 delay,
                 run_now,
                 # loader job
                 mongodb,
                 mongo_klg,
                 name,
                 failed,
                 chain_id,
                 batch_size,
                 max_workers,
                 ):
        scheduler = f"^{run_now}@{interval}/{delay}#true"
        super().__init__(scheduler)
        self.mongodb = mongodb
        self.mongo_klg = mongo_klg
        self.name = name
        self.failed = failed
        self.chain_id = chain_id
        self.batch_size = batch_size
        self.max_workers = max_workers


    def _execute(self, *args, **kwargs):
        cursor =self.mongo_klg._db['smart_contracts'].find({"chainId": self.chain_id, "idCoingecko":{"$exists":True},  "price":{"$gt":0}, "marketCap":{"$gt":1000000}})
        token_list = []
        columns = ['_id','address','idCoingecko']
        if self.failed == None:
            for c in cursor:
                token_list.append({key: c.get(key) for key in columns})
        else:
            try:
                tokens = []
                with open(f'data/log_file/failed_tokens/failed_{self.chain_id}_tokens/failed_tokens.json') as file:
                    for failed_token in file:
                        failed_addresses = json.loads(failed_token)
                        tokens.append(failed_addresses)
            except Exception as e:
                logger.info(e)
                logger.info(f"{self.chain_id} does not have failed top tokens addresses")
                return

            for token in tokens:
                token_info_dct = dict()
                token_info = list(self.mongo_klg._db['smart_contracts'].find({'_id':f'{self.chain_id}_{token}'}))[0]
                token_info_dct['_id'] = token_info['_id']
                token_info_dct['address'] = token_info['address']
                token_info_dct['idCoingecko'] = token_info['idCoingecko']
                token_list.append(token_info_dct)


        job = GetTokenPrice(exporter=self.mongodb, 
                            name=self.name, 
                            chain_id=self.chain_id, 
                            token_addresses=token_list,
                            batch_size=self.batch_size,
                            max_workers=self.max_workers)
        job.run()




