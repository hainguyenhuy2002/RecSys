import click
from services.get_address_service import GetAddress
from databases.mongodb_entity import MongoDBEntity
from databases.mongodb import MongoDB
from databases.arangodb_klg import ArangoDB
@click.command(context_settings=dict(help_option_names=['-h', '--help']))

@click.option('-n', '--name', type=str,
              help='Folder path to save training data file')
@click.option('-b', '--batch-size', type=int, default=1, show_default=True,
              help='Batch size - number of addresses each worker processes')
@click.option('-w', '--max-workers', default=8, show_default=True, type=int,
              help='The number of workers')
def get_address(name, batch_size, max_workers):

    mongoKlg = MongoDBEntity()
    mongoKlg_wallets = mongoKlg.wallets
    mongoSubgraph = MongoDB()
    arangoDb = ArangoDB()
    flagged_lst = [i for i in range(1,10)]
    job = GetAddress(importer=mongoKlg_wallets,
                     arangoDb= arangoDb,
                     exporter=mongoSubgraph,
                     name=name,
                     flagged_lst=flagged_lst, 
                     max_workers=max_workers, 
                     batch_size=batch_size)
    job.run()
