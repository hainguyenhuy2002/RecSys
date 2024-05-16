from typing import List, Dict
import sys
import os
import time
import signal


sys.path.append(os.path.dirname(sys.path[0]))

from arango import ArangoClient
from arango.database import StandardDatabase
from arango.http import DefaultHTTPClient
from arango.result import Result

from config import ArangoDBConfig
from constants.arangodb_constants import ArangoDBCollectionsByChain, ArangoDBGraphsByChain, KnowledgeGraphModelByChain
from utils.logger_utils import get_logger
from utils.parser import get_connection_elements

from constants.arangodb_constants import (ArangoDBCollections, ArangoDBGraphs, KnowledgeGraphModel,
                                          ArangoDBPrefix,
                                          ArangoDBCollectionsByChain, ArangoDBGraphsByChain, KnowledgeGraphModelByChain)
from utils.logger_utils import get_logger
from utils.parser import get_connection_elements

logger = get_logger('ArangoDB')


class ArangoDB:
    def __init__(self, connection_url=None, database=ArangoDBConfig.DATABASE, prefix: str = None):
        if not connection_url:
            connection_url = ArangoDBConfig.CONNECTION_URL
        _username, _password, _connection_url = get_connection_elements(connection_url)

        # http_client = DefaultHTTPClient()
        # http_client.REQUEST_TIMEOUT = 1000
        print(_username)
        print(_password)
        print(_connection_url)
        try:
            self.client = ArangoClient(hosts=_connection_url)
        except Exception as e:
            logger.exception(f"Failed to connect to ArangoDB: {_connection_url}: {e}")
            sys.exit(1)

        self._db = self._get_db(database, _username, _password)


    def _get_db(self, db_name, username, password):
        return self.client.db(db_name, username=username, password=password)

    def _get_graph(self, graph_name, edge_definitions=KnowledgeGraphModel.edge_definitions,
                   database: StandardDatabase = None):
        if not database:
            database = self._db
        if not database.has_graph(graph_name):
            database.create_graph(graph_name, edge_definitions=edge_definitions)
        return database.graph(graph_name)

    def _get_collections(self, collection_name, database: StandardDatabase = None, edge=False):
        if not database:
            database = self._db
        if not database.has_collection(collection_name):
            database.create_collection(collection_name, shard_count=20, edge=edge)
        return database.collection(collection_name)

    #####################
    #     Retrieve      #
    #####################
    def get_num_send_receive(self, wallet):

        # Define your AQL query with conditions
        aql_query = '''
            FOR doc IN ethereum_addresses
            FILTER doc._id IN @value
            RETURN { 
                address: doc.address,
                numberSent: doc.numberSent,
                numberReceived: doc.numberReceived,
            }
        '''
        cursor = self._db.aql.execute(aql_query, bind_vars={'value':wallet})
        cur = [doc for doc in cursor]
        return cur

    def get_number_of_relationships(self):
        return len(self._transfers_col)

    def get_token_transfers(self, skip, limit):
        return self._transfers_col.all(skip=skip, limit=limit)

    def check_has_relationship(self, edge_key: str):
        edge_id = f"{self._prefix}_transfers/{edge_key}"
        try:
            assert edge_id in self._transfers_col
            return True
        except AssertionError:
            return False

    @staticmethod
    def _parse_id(id_string):
        return id_string.split('/')[-1]
    
    def query(self, query: str, batch_size=1000) -> Result:
        return self._db.aql.execute(query=query, batch_size=batch_size)


if __name__ == '__main__':
    chain_id = '0x38'
    arango = ArangoDB(prefix='bsc')
    # c = arango.check_has_relationship('0x38_0x9e3698dd688cb51cb27a0aff7b06575f6953bc47_0x0f2c174dd2d0a7e808a650ed4778970ed48b11e6')
    c = arango.check_has_relationship('0x38_sss_sss')
    print(c)
