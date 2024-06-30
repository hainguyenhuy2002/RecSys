import click
import json
from utils.logger_utils import get_logger
from utils.generate_training_utils import get_tags
from databases.mongodb import MongoDB
from databases.mongodb_entity import MongoDBEntity
from cli_scheduler.scheduler_job import SchedulerJob
from services.generate_training_data_service import GenerateData
from constants.dapps_tokens_constans import Dapps
from constants.time_constants import TimeConstants

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-s', '--searching_address', type=str, default='', show_default=True,
              help='address searching mongoDb')
@click.option('-n', '--name', type=str, default=None, show_default=True,
              help='name collection')
@click.option('-d', '--direction', type=str,
              help='train or search')
@click.option('-t', '--timestamp', type=int, default=1711421985)
@click.option('-b', '--batch-size', type=int)
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')
@click.option('-i', '--interval', default=TimeConstants.A_DAY, show_default=True, type=int,
              help='Interval to repeat the job')
@click.option('--delay', default=0, show_default=True, type=int, help='Time (in seconds) to delay')
@click.option('--run-now', default=True, show_default=True, type=bool,
              help='False to wait until interval then run')

def generate_training_data_daily(searching_address, name, direction, timestamp, batch_size, max_workers, interval, delay, run_now):
    job = GenerateTrainingDataSchedulerJob(interval=interval,
                                      delay=delay,
                                      run_now=run_now,
                                      searching_address=searching_address,
                                      name=name,
                                      direction=direction,
                                      timestamp=timestamp,
                                      batch_size=batch_size,
                                      max_workers=max_workers)
    job.run()
    



class GenerateTrainingDataSchedulerJob(SchedulerJob):
    def __init__(self,
                 # scheduler job
                 interval,
                 delay,
                 run_now,
                 # loader job
                 searching_address,
                 name, 
                 direction, 
                 timestamp, 
                 batch_size, 
                 max_workers
                 ):
        scheduler = f"^{run_now}@{interval}/{delay}#true"
        super().__init__(scheduler)
        self.searching_address = searching_address
        self.name = name
        self.direction = direction
        self.timestamp = timestamp
        self.batch_size = batch_size
        self.max_workers = max_workers

    def _execute(self, *args, **kwargs):
        generate_training_data(searching_address=self.searching_address,
                               name=self.name,
                               direction=self.direction,
                               timestamp=self.timestamp,
                               batch_size=self.batch_size,
                               max_workers=self.max_workers
                              )

def generate_training_data(searching_address, name, direction, timestamp, batch_size, max_workers):

    mongodb = MongoDB()
    klg = MongoDBEntity()
    col_lst = mongodb._db.list_collection_names()
    address_searching = mongodb._db[f'{searching_address}']

    largest_flag = mongodb.get_largest_flag(db='wallet_exchanges') +1
    flagged_lst = [i for i in range(1, largest_flag)]
    num_flags = len(flagged_lst)



    if direction == 'train':
        largest_batch = mongodb.get_largest_batch(db='potential_training_features')
        dapps_name_lst = Dapps().all_projects
        logger = get_logger('Generate data process')
        logger.info(f'Gen training for {dapps_name_lst}')
        for dapps_name in dapps_name_lst:
            logger.info(f"-------------------------------------------------------------------------------------")
            logger.info(f"training data for {dapps_name} ")
            dapps_tags = Dapps(dapps_name=dapps_name).tags
            logger.info('start to generate training address')
            ## get lending tags - depositors, borrowers
            lending_tags = get_tags(dapps_tags)
            Dapps_user_addresses = []
            interacted_addresses = []
            training_cursor = address_searching.find({'lattestTags':{'$in':dapps_tags}})  
            for cur in training_cursor:
                Dapps_user_addresses.append(cur['_id'])
                wallet_interact_lst = cur['interactedWallet'].keys()
                prefixed_list = list(map(lambda x: cur['chainId']+'_' + x, wallet_interact_lst))
                interacted_addresses.extend(prefixed_list)
            logger.info('Start to get training data')
            ## get dapps users label
            job1 = GenerateData(importer=address_searching, 
                            exporter=mongodb, 
                            klg=klg,
                            dapps_name=dapps_name, 
                            direction=direction, 
                            index_lst=Dapps_user_addresses, 
                            timestamp=timestamp, 
                            lending_tags=lending_tags,
                            name=name,
                            batch=largest_batch-1,
                            interacted_addresses=list(set(interacted_addresses)),
                            max_workers=max_workers, 
                            batch_size=batch_size)
            job1.run()



            logger.info('Done ( ๑ ˃̵ᴗ˂̵)و ♡ ( ๑ ˃̵ᴗ˂̵)و ♡')

    elif direction =='search':
        logger = get_logger(f'Gen searching for multichain')
        # largest_flag = mongodb.get_largest_flag(db='wallet_exchanges') +1
        # flagged_lst = [i for i in range(1, largest_flag)]
        # num_flags = len(flagged_lst)
        logger.info(f"start to search with {num_flags} flags")

        if name not in col_lst:
            direction = 'search first' 
            job =GenerateData(importer=address_searching, 
                            exporter= mongodb,
                            klg = klg, 
                            direction=direction, 
                            index_lst=flagged_lst, 
                            timestamp=timestamp, 
                            name=name,
                            batch=0,
                            max_workers=max_workers, 
                            batch_size=batch_size)
            job.run()

        else:
            largest_batch = mongodb.get_largest_batch(db=name)
            direction = 'search continue' 
            job =GenerateData(importer=address_searching, 
                            exporter= mongodb,
                            klg = klg, 
                            direction=direction, 
                            index_lst=flagged_lst, 
                            timestamp=timestamp, 
                            batch=largest_batch,
                            name=name,
                            max_workers=max_workers, 
                            batch_size=batch_size)
            job.run()
