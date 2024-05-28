from services.get_address_service import GetAddress
from services.transaction_info_service import GetTransactionInfoService
from databases.mongodb_entity import MongoDBEntity
from databases.mongodb import MongoDB
from databases.mongodb_main import MongoDBMain
from constants.network_constants import Chains
from utils.list_dict_utils import get_special_wallet_list
from utils.history_price_utils import query_historical_prices
from utils.logger_utils import get_logger


def get_exchange_info_service(name, wallets_per_job, hot_path, burn_mint_path, token_price, batch_size, max_workers, daily=False):
    logger = get_logger("Start to get addresses exchange info")
    ## get chains
    chain_names = Chains.all_name
    chains =Chains.alls
    logger.info(f"Query chains: {chain_names}")
    ## get special wallet list
    logger.info(f"Getting special wallets ...")
    special_wallet_lst = get_special_wallet_list(hot_path=hot_path, 
                                             burn_mint_path=burn_mint_path)
    
    ## connect to databases 
    logger.info("Connecting to databases: postgre, klg, community ...")
    try:
        mongo_klg = MongoDBEntity()
        mongo_klg_wallets = mongo_klg.wallets
        mongo_community = MongoDB()
        logger.info("Done!!!")
    except Exception as e:
        logger.info("Error in databases connection job")
    
    ## get token price
    logger.info("Query token price ...")
    historical_token_price = query_historical_prices(mongo_community=mongo_community,
                                                     token_price=token_price,
                                                     chains=chains)


    ## connect to mongo main, timestamp, get the multichain info 
    logger.info("Getting multichain info: chainId, start/end timestamp, start/end block")
    multichain_transaction = dict()
    if daily == False:
        try:
            for chain in chain_names:
                chain_id = Chains.mapping[chain]
                chain_info_update = dict()
                chain_info = dict()
                mongo_transaction = MongoDBMain(chain=chain)
                #postgre = PostgresDB(chain_id=chain_id)
                if chain in ['bsc', 'ethereum', 'polygon']:
                    for start_block, start in mongo_transaction.get_previous_3month_block().items():
                        start_block = start_block
                        start = start
                    for end_block, end in mongo_transaction.get_largest_block().items():
                        end_block = end_block
                        end = end
                else:
                    for start_block, start in mongo_transaction.get_previous_1month_block().items():
                        start_block = start_block
                        start = start
                    for end_block, end in mongo_transaction.get_largest_block().items():
                        end_block = end_block
                        end = end

                block_timestamp_mappings = mongo_transaction.get_block_number_to_timestamp(start_block=start_block, end_block=end_block)
                chain_info['start'] = start
                chain_info['end'] = end
                chain_info['start_block'] = start_block 
                chain_info['end_block'] = end_block
                chain_info['block_timestamp_mappings'] = block_timestamp_mappings
                chain_info_update[f'{chain_id}'] = chain_info
                multichain_transaction.update(chain_info_update)
        except Exception as e:
            logger.info("Error in multichain transaction info job")
            logger.info(e)

        successful_chains = multichain_transaction.keys()
        logger.info(f"Successful to get fully chain info of {successful_chains}!!!")


    else:
        try:
            for chain in chain_names:
                chain_id = Chains.mapping[chain]
                chain_info_update = dict()
                chain_info = dict()
                mongo_transaction = MongoDBMain(chain=chain)
                #postgre = PostgresDB(chain_id=chain_id)
                if chain in ['bsc', 'ethereum', 'polygon']:
                    for start_block, start in mongo_transaction.get_previous_2day_block().items():
                        start_block = start_block
                        start = start
                    for end_block, end in mongo_transaction.get_largest_block().items():
                        end_block = end_block
                        end = end
                else:
                    for start_block, start in mongo_transaction.get_previous_1month_block().items():
                        start_block = start_block
                        start = start
                    for end_block, end in mongo_transaction.get_largest_block().items():
                        end_block = end_block
                        end = end

                block_timestamp_mappings = mongo_transaction.get_block_number_to_timestamp(start_block=start_block, end_block=end_block)
                chain_info['start'] = start
                chain_info['end'] = end
                chain_info['start_block'] = start_block 
                chain_info['end_block'] = end_block
                chain_info['block_timestamp_mappings'] = block_timestamp_mappings
                chain_info_update[f'{chain_id}'] = chain_info
                multichain_transaction.update(chain_info_update)
        except Exception as e:
            logger.info("Error in multichain transaction info job")
            logger.info(e)

        successful_chains = multichain_transaction.keys()
        logger.info(f"Successful to get daily chain info of {successful_chains}!!!")


    largest_flag = mongo_klg.get_largest_flag() +1
    flagged_lst = [i for i in range(1, largest_flag)]
    flagged_lst = [1, 2]
    exchange_service = GetTransactionInfoService(
                             mongo_community=mongo_community,
                             historical_token_price=historical_token_price,
                             multichain_transaction=multichain_transaction,
                             special_wallets=special_wallet_lst,
                             filename=name)

    logger.info("Start jobs")

    job = GetAddress(importer=mongo_klg_wallets,
                     exporter=mongo_community,
                     hot_wallets=special_wallet_lst,
                     name=name,
                     wallets_per_job=wallets_per_job,
                     exchange_service=exchange_service,
                     flagged_lst=flagged_lst, 
                     max_workers=max_workers, 
                     batch_size=batch_size)
    job.run()
