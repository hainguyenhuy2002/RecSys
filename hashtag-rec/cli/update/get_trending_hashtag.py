import click
import json
import pandas as pd
import time

from databases.mongodb import MongoDB
from jobs.cli_job import CLIJob
from collections import Counter
from constant.twitter_constant import Dapps
from constant.time_constant import TimeConstants
from utils.logger_utils import get_logger
from utils.preprocess_text_utils import preprocess_tweet

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-i', '--interval', default=TimeConstants.A_DAY, show_default=True, type=int)
@click.option('-pe', '--period', default=TimeConstants.A_DAY, show_default=True, type=int)
@click.option('-li', '--limit', default=None, type=int)
@click.option('-d', '--dapps-name', default='world', show_default=True, type=str,
              help='name of dapps to update keywords')
@click.option('-n', '--name', default='trava', show_default=True, type=str,
              help='name of collection to update')
@click.option('-k', '--kw-num', default=30, show_default=True, type=int,
              help='number of generating keyWords')


def get_trending_hashtag(interval, period, limit, dapps_name, name, kw_num):
    db = MongoDB()
    dapps = Dapps(dapps_name=dapps_name)
    dapps_followers = dapps.following
    job = UpdateTrendingKeyWords(
        interval=interval,
        period=period,
        limit=limit,
        db=db,
        dapps_followers=dapps_followers,
        dapps_name=dapps_name,
        name=name,
        kw_num=kw_num
        )
    job.run()
class UpdateTrendingKeyWords(CLIJob):
    def __init__(self, interval, period, limit, db, dapps_followers, dapps_name, name, kw_num):
        super().__init__(interval, period, limit, retry=False)
        self.db = db
        self.dapps_name = dapps_name
        self.name = name
        self.kw_num = kw_num
        self.dapps_followers = dapps_followers

    def _execute(self):
        log = get_logger("Trending keywords process")
        log.info("Start to get tweets info ...")
        lattest_tweets = self.db.get_latest_tweets()
        log.info("Sucessful!")
        df_twitter = pd.DataFrame(lattest_tweets)
        log.info("Start to preprocess key words ...")

        df_clean = preprocess_tweet(df_twitter)
        if len(self.dapps_followers)> 0:
            dapps_trending = df_clean[df_clean['authorName'].isin(self.dapps_followers)]
        else:
            dapps_trending = df_clean.copy()
        log.info("Sucessful!")
        log.info("Start to flatten to dictionary form and update to Mongo")
        trending_keyword = dapps_trending.groupby('keyWordsClean').agg({'count':'count'}).reset_index()
        trending_keyword = trending_keyword.sort_values('count', ascending=False).reset_index(drop=True)
        trendings = trending_keyword.iloc[0:self.kw_num]
        trending_dct = trending_keyword.to_dict()
        trends = dict()
        for i in range(0, len(trendings)):
            keywords = trending_dct['keyWordsClean'][i]
            count = trending_dct['count'][i]
            trends[f'{keywords}'] = count
        
        trends_info = dict()
        trends_info['_id'] = self.dapps_name
        now_time = int(time.time()) -(int(time.time()) %86400)
        trends_info[f'{now_time}'] = trends
        trends_info['lastTimestamp'] = now_time
        self.db.update_docs(
            collection_name=self.name, 
            data=[trends_info]
            )
        log.info("Sucessful!")
