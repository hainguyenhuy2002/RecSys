import click

from databases.mongodb import MongoDB
from utils.logger_utils import get_logger
from services.get_exchange_info_service import get_exchange_info_service
from cli_scheduler.scheduler_job import SchedulerJob
from constants.time_constants import TimeConstants

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-n', '--name', type=str,
              help='Folder path to save training data file')
@click.option('--interval', default=TimeConstants.A_DAY, show_default=True, type=int,
              help='Interval to repeat the job')
@click.option('--delay', default=0, show_default=True, type=int, help='Time (in seconds) to delay')
@click.option('--run-now', default=True, show_default=True, type=bool,
              help='False to wait until interval then run')

def get_flagged_daily(name, interval, delay, run_now):
    job = GetFlaggedDailyJob(interval=interval,
                                      delay=delay,
                                      run_now=run_now,
                                      importer=MongoDB(),
                                      name=name,)
    job.run()
    


class GetFlaggedDailyJob(SchedulerJob):
    def __init__(self,
                 # scheduler job
                 interval,
                 delay,
                 run_now,
                 # loader job
                 importer,
                 name
                 ):
        scheduler = f"^{run_now}@{interval}/{delay}#true"
        super().__init__(scheduler)
        self.mongo_community = importer
        self.name = name


    def _execute(self, *args, **kwargs):
        cursor = self.mongo_community._db[f'{self.name}'].find({'flagged':{'$exists':False}}, {'_id':1})
        non_flag_info_lst =[]
        a = 0
        largest_flag = MongoDB().get_largest_flag(f'{self.name}')
        flag_lst = []
        for cur in cursor:
            if a%100 ==0:
                largest_flag+=1
                flag_lst.append(largest_flag)
                if a>1:
                    self.mongo_community.update_docs(collection_name=self.name, data=non_flag_info_lst, merge=True)  
                    non_flag_info_lst =[]
            cur['flagged'] = largest_flag
            non_flag_info_lst.append(cur)
            a+=1
        if len(non_flag_info_lst) >0:
            flag_lst.append(largest_flag)
            self.mongo_community.update_docs(collection_name=self.name, data=non_flag_info_lst, merge=True)  

        start_flag = flag_lst[0]
        end_flag = flag_lst[-1]
        print(f"Sucessful update flag from {start_flag} to {end_flag} ")
        
