from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List, Dict

from config import PostgresDBConfig
from utils.logger_utils import get_logger

logger = get_logger('PostgreSQL thread safe')

Session = sessionmaker()


class PostgresDB:
    def __init__(self, connection_url: str = None):
        # Set up the database connection and create the table
        if not connection_url:
            connection_url = PostgresDBConfig.CONNECTION_URL
        Session.configure(bind=create_engine(connection_url))

    @staticmethod
    def query_addresses(addresses, direction, from_block, to_block, chain_id):
        if not chain_id:
            schema = PostgresDBConfig.SCHEMA
        else:
            schema = f"chain_{chain_id}"
        addresses_values = ', '.join([f"'{cls}'" for cls in addresses])

        query = f"""
            SELECT contract_address, block_number, from_address, to_address, value
            FROM {schema}.{PostgresDBConfig.TRANSFER_EVENT_TABLE}
            WHERE {direction}_address IN ({addresses_values})
            AND block_number BETWEEN {from_block} AND {to_block}
        """
        with Session.begin() as session:
            event_transfer = session.execute(query).all()
        return event_transfer

