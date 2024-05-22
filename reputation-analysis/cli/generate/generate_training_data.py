import click
import json
from utils.logger_utils import get_logger
from databases.mongodb import MongoDB
from databases.mongodb_entity import MongoDBEntity
from services.generate_training_data_service import GenerateData
from constants.dapps_tokens_constans import Dapps
@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('-s', '--searching_address', type=str, default='', show_default=True,
              help='address searching mongoDb')
@click.option('-da', '--dapps_name', type=str, default=None, show_default=True,
              help='name of an dapps')
@click.option('-d', '--direction', type=str,
              help='train or search')
@click.option('-t', '--time-stamp', type=int, default=1711421985)
@click.option('-b', '--batch-size', type=int)
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')

def generate_training_data(searching_address, dapps_name, direction, time_stamp, batch_size, max_workers):

    mongodb = MongoDB()
    klg = MongoDBEntity()
    address_searching = mongodb._db[f'{searching_address}']
    if direction == 'train':
        dapps_tags = Dapps(dapps_name=dapps_name).tags
        logger = get_logger('Gen training')
        logger.info('༼ つ ◕_◕ ༽つ ༼ つ ◕_◕ ༽つ start to generate training address ༼ つ ◕_◕ ༽つ ༼ つ ◕_◕ ༽つ')
        # with open(address_dapps,'r') as file:
        #     Dapps_user_address = json.load(file)
        Dapps_user_address = []
        training_cursor = address_searching.find({'lattestTags':{'$in':dapps_tags}})  
        for cur in training_cursor[0:100]:
            Dapps_user_address.append(cur['_id'])
    
        logger.info('Successful get training addresses ( ˵ •̀ ᴗ •́˵) ( ˵ •̀ ᴗ •́˵)')
        index_list = list(range(batch_size, len(Dapps_user_address), batch_size))
        index_list.append(len(Dapps_user_address))
        logger.info('༼ つ ◕_◕ ༽つ ༼ つ ◕_◕ ༽つ start to get training data༼ つ ◕_◕ ༽つ ༼ つ ◕_◕ ༽つ')
        job =GenerateData(importer=address_searching, 
                          exporter=mongodb, 
                          klg=klg,
                          dapps_name=dapps_name, 
                          direction=direction, 
                          index_lst=index_list,
                          Dapps_user_addresses=Dapps_user_address, 
                          timestamp=time_stamp, 
                          max_workers=max_workers, 
                          batch_size=batch_size)
        job.run()



        logger.info('Done ( ๑ ˃̵ᴗ˂̵)و ♡ ( ๑ ˃̵ᴗ˂̵)و ♡')
    elif direction =='search':
        num_documents = address_searching.estimated_document_count()
        index_list = list(range(batch_size, num_documents, batch_size))
        index_list.append(num_documents)
        job =GenerateData(importer=address_searching, 
                          exporter= mongodb,
                          klg = klg, 
                          direction=direction, 
                          index_lst=index_list, 
                          timestamp=time_stamp, 
                          max_workers=max_workers, 
                          batch_size=batch_size)
        job.run()
    
