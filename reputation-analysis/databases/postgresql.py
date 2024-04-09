import bisect
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from config import PostgresDBConfig
from utils.logger_utils import get_logger

logger = get_logger('PostgreSQL thread safe')

Session = sessionmaker()

def largest_key_smaller_than(dictionary, value):
    keys = sorted(dictionary.keys())
    index = bisect.bisect_left(keys, value) - 1
    if index >= 0:
        return keys[index]
    else:
        return 0

def get_valueInUSD(row, token_history, token_lst, block_timestamp_mappings):
    token = row[0] #contract
    if token in token_lst:
        if token_history[token] != {}:
            timestamp = row[1]
            round_timestamp = ((block_timestamp_mappings[timestamp]  - block_timestamp_mappings[timestamp]  % 86400))  #change to timestamp daily, not times 1000
            if f'{round_timestamp}' in list(token_history[token].keys()):
                valueInUSD = (row[-1]) * token_history[token][f'{round_timestamp}']
            else:
                largest_key = largest_key_smaller_than(token_history[token], str(round_timestamp))
                if largest_key ==0:
                    valueInUSD = 0
                else:
                    last_value = token_history[token][largest_key]
                    valueInUSD = (row[-1]) * last_value
                valueInUSD = 0
            return valueInUSD
        else:
            return None
    else: 
        return None

class PostgresDB:
    def __init__(self, connection_url: str = None):
        # Set up the database connection and create the table
        if not connection_url:
            connection_url = PostgresDBConfig.CONNECTION_URL
        Session.configure(bind=create_engine(connection_url))

    @staticmethod
    def query_addresses(addresses, special_addresses, direction, opposite_direction, from_block, to_block, chain_id, block_timestamp_mappings ,price_history):
        token_lst = [token for token, _ in price_history.items()]
        if not chain_id:
            schema = PostgresDBConfig.SCHEMA
        else:
            schema = f"chain_{chain_id}"
        addresses_values = ', '.join([f"'{cls}'" for cls in addresses])
        special_addresses_values = ', '.join([f"'{cls}'" for cls in special_addresses])

        query = f"""
            SELECT contract_address, block_number, from_address, to_address, value
            FROM {schema}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
            WHERE {direction}_address IN ({addresses_values})
            AND {opposite_direction}_address NOT IN ({special_addresses_values})
            AND block_number BETWEEN {from_block} AND {to_block}
        """
        count_query =f"""
            SELECT COUNT(*)
            FROM  {schema}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
            WHERE {direction}_address IN ({addresses_values});
            AND block_number BETWEEN {from_block} AND {to_block}
        """
        with Session.begin() as session:
            wallet_transfer = []
            failed_addresses = []
            try:
                num_event = session.execute(text(count_query)).fetchone()[0]
                if num_event >= 30000:
                    for address in addresses:
                        query_v2 = f"""
                        SELECT contract_address, block_number, from_address, to_address, value
                        FROM {schema}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
                        WHERE {direction}_address={address}
                        AND {opposite_direction}_address NOT IN ({special_addresses_values})
                        AND block_number BETWEEN {from_block} AND {to_block}
                        """
                        count_query_v2 =f"""
                            SELECT COUNT(*)
                            FROM  {schema}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
                            WHERE {direction}_address IN ({addresses_values});
                            AND block_number BETWEEN {from_block} AND {to_block}
                        """

                        num_event_v2 = session.execute(text(count_query_v2)).fetchone()[0]
                        if num_event_v2 >1500:
                            failed_addresses.append(address)
                            continue
                        else:
                            event_transfer = session.execute(text(query_v2))
                            fields_to_select =['contract_address', 'block_number', 'from_address', 'to_address', 'value']
                            for event in event_transfer:
                                valueInUSD = get_valueInUSD(row = event, token_history =price_history,token_lst = token_lst, block_timestamp_mappings=block_timestamp_mappings)
                                modified_event = event[:1] + (block_timestamp_mappings[event[1]],) + event[2:]
                                timestamp_event = dict(zip(fields_to_select, modified_event))
                                timestamp_event['valueInUSD'] = valueInUSD
                                wallet_transfer.append(timestamp_event)

                else:
                    event_transfer = session.execute(text(query))
                    fields_to_select =['contract_address', 'block_number', 'from_address', 'to_address', 'value']
                    for event in event_transfer:
                        valueInUSD = get_valueInUSD(row = event, token_history =price_history,token_lst = token_lst, block_timestamp_mappings=block_timestamp_mappings)
                        modified_event = event[:1] + (block_timestamp_mappings[event[1]],) + event[2:]
                        timestamp_event = dict(zip(fields_to_select, modified_event))
                        timestamp_event['valueInUSD'] = valueInUSD
                        wallet_transfer.append(timestamp_event)

            except Exception as e:
                log =get_logger("Oh no getting an error in the query Postgres task")
                log.info(addresses)
                log.info(e)
                wallet_transfer = []
                
        return wallet_transfer
