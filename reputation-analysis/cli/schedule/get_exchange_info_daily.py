import click

from services.get_exchange_info_service import get_exchange_info_service
from cli_scheduler.scheduler_job import SchedulerJob
from constants.time_constants import TimeConstants

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-n', '--name', type=str,
              help='Folder path to save training data file')
@click.option('-wj', '--wallets-per-job', type=int,
              help='number of proccessed wallets per job')
@click.option('-h', '--hot-path', type=str,
              help='input of hot wallet')
@click.option('-bm', '--burn-mint-path', type=str,
              help='input of hot wallet')
@click.option('-tp', '--token-price', type=str,
              help='collection to store token price')
@click.option('-b', '--batch-size', type=int, default=1, show_default=True,
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')
@click.option('--interval', default=TimeConstants.A_DAY, show_default=True, type=int,
              help='Interval to repeat the job')
@click.option('--delay', default=0, show_default=True, type=int, help='Time (in seconds) to delay')
@click.option('--run-now', default=True, show_default=True, type=bool,
              help='False to wait until interval then run')



def get_exchange_info_daily(name, wallets_per_job, hot_path, burn_mint_path, token_price, batch_size, max_workers, interval, delay, run_now):
    job = CrawlTokenPriceSchedulerJob(interval=interval,
                                      delay=delay,
                                      run_now=run_now,
                                      name=name,
                                      wallets_per_job=wallets_per_job,
                                      hot_path=hot_path,
                                      burn_mint_path=burn_mint_path,
                                      token_price=token_price,
                                      batch_size=batch_size,
                                      max_workers=max_workers)
    job.run()
    



class CrawlTokenPriceSchedulerJob(SchedulerJob):
    def __init__(self,
                 # scheduler job
                 interval,
                 delay,
                 run_now,
                 # loader job
                 name, 
                 wallets_per_job, 
                 hot_path, 
                 burn_mint_path, 
                 token_price, 
                 batch_size, 
                 max_workers
                 ):
        scheduler = f"^{run_now}@{interval}/{delay}#true"
        super().__init__(scheduler)
        self.name = name
        self.wallets_per_job = wallets_per_job
        self.hot_path = hot_path
        self.burn_mint_path = burn_mint_path
        self.token_price = token_price
        self.batch_size = batch_size
        self.max_workers = max_workers


    def _execute(self, *args, **kwargs):
        get_exchange_info_service(name=self.name,
                              wallets_per_job=self.wallets_per_job,
                              hot_path=self.hot_path,
                              burn_mint_path=self.burn_mint_path,
                              token_price=self.token_price,
                              batch_size=self.batch_size,
                              max_workers=self.max_workers,
                              daily=True
                              )