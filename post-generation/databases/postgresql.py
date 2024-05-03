from sqlalchemy.orm import sessionmaker
from config import PostgresRAGDBConfig
from utils.logger_utils import get_logger
from utils.postgres_utils import extract_db_details
# from llama_index.vector_stores.postgres import PGVectorStore

logger = get_logger('PostgreSQL thread safe')
Session = sessionmaker()


class PostgresDB:
    def __init__(self, connection_url: str = None):
        # Set up the database connection and create the table
        if not connection_url:
            connection_url = PostgresRAGDBConfig.CONNECTION_URL
        self.db_name, self.host, self.password, self.port, self.user = extract_db_details(connection_url)
        self.vetor_store = PGVectorStore.from_params(
                                database=self.db_name,
                                host=self.host,
                                password=self.password,
                                port=self.port,
                                user=self.user,
                                table_name=PostgresRAGDBConfig.EMBEDDING_TABLE,
                                embed_dim=384)

    @staticmethod
    
    def upload_vector_db(self, vector_data):
        vector_store=self.vetor_store
        vector_store.add(vector_data)

    # def query_vector_db(self, EmbedModel, input):
    #     query_embedding = EmbedModel.get_query_embedding(input)
    #     query_mode = "default"
    #     vector_store_query = VectorStoreQuery(
    #     query_embedding=query_embedding, similarity_top_k=3, mode=query_mode
    #     )

    #     query_result = vector_store.query(vector_store_query)
    #     for i in range(0, 3):
    #         print(query_result.nodes[i].get_content())
