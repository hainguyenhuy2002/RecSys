import click
import json
from utils.logger_utils import get_logger
from databases.mongodb import MongoDB
from multithread_processing.base_job import BaseJob
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-co', '--col', type=str, default='', show_default=True,
              help='address searching mongoDb')
@click.option('-w', '--max_workers', default=4, show_default=True, type=int,
              help='The number of workers')
@click.option('-b', '--batch_size', default=500, show_default=True, type=int,
              help='The number of workers')
def update_tags(col, max_workers, batch_size):

    mongodb = MongoDB()
    num_document = mongodb.count_documents(f'{col}')
    index_lst = list(range(batch_size, num_document, batch_size))
    index_lst.append(num_document)

    job = UpdateTagsServices(mongodb=mongodb,
                             col=col,
                             index_lst=index_lst,
                             max_workers=max_workers,
                             batch_size=batch_size)
    job.run()


class UpdateTagsServices(BaseJob):
    def __init__(self,  mongodb, col, index_lst, max_workers= 4, batch_size=1000):
        self.mongodb = mongodb
        self.batch_size = batch_size
        self.col = col
        super().__init__(work_iterable=index_lst,
                         max_workers=max_workers,
                         batch_size=batch_size)

    def _execute_batch(self, works):
        for work in works:    
            cursor = self.mongodb._db[f'{self.col}'].find()
            address_lst =[]
            for cur in cursor[work-self.batch_size: work]:
                if 'tags' in cur:
                    for timestamp, tags in cur['tags'].items():
                        cur['lattestTags'] = tags
                        address_lst.append(cur)
            self.mongodb.update_docs(collection_name=self.col,
                                     data=address_lst, merge=True)
        
    def _end(self):
        super()._end()        

