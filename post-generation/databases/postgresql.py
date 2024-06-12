from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text
from config import PostgresRAGDBConfig, EmbeddingModelConfig
from models.embedding_models import EmbeddingModel
from utils.logger_utils import get_logger
from utils.postgres_utils import extract_db_details
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.schema import TextNode
from constant.time_constant import TimeConstants

import json
import time

logger = get_logger('PostgreSQL thread safe')
Session = sessionmaker()

class Columns:
    ID = 'id'
    TEXT = 'text'
    METADATA = 'metadata_'
    NODE_ID = 'node_id'
    EMBEDDING = 'embedding'
    TIMESTAMP = 'timestamp'
    AUTHOR = 'author'


class PostgresDB:
    def __init__(self, connection_url: str = None):
        # Set up the database connection and create the table
        if not connection_url:
            connection_url = PostgresRAGDBConfig.CONNECTION_URL
        self.db_name, self.host, self.password, self.port, self.user = extract_db_details(connection_url)
        self.vector_store = PGVectorStore.from_params(
            database=self.db_name,
            host=self.host,
            password=self.password,
            port=self.port,
            user=self.user,
            table_name=PostgresRAGDBConfig.RAG_TABLE,
            embed_dim=int(EmbeddingModelConfig.EMBEDDING_DIMENSION)
        )
        self.vector_store_v2 = PGVectorStore.from_params(
            database=self.db_name,
            host=self.host,
            password=self.password,
            port=self.port,
            user=self.user,
            table_name=PostgresRAGDBConfig.RAG_TABLE_V2,
            embed_dim=int(EmbeddingModelConfig.EMBEDDING_DIMENSION)
        )
        self.engine = create_engine(connection_url)
        self.session = Session(bind=self.engine)

    def table_exists(self, table_name):
        """Check if a table exists in the database."""
        inspector = inspect(self.engine)
        return inspector.has_table(table_name)

    def ensure_unique_constraint(self, table):
        """Ensure the node_id column has a unique constraint."""
        with self.session.begin():
            alter_query = text(f"""
            ALTER TABLE {table}
            ADD CONSTRAINT {table}_node_id UNIQUE ({Columns.NODE_ID})
            """)
            self.session.execute(alter_query)
            logger.info("Unique constraint on node_id added successfully.")
        
        self.session.commit()
        self.session.close()

    def add_timestamp_column(self, table):
        """Add a timestamp column to the table if it doesn't already exist."""
        try:
            with self.session.begin():
                add_timestamp_column_query = text(f"""
                ALTER TABLE {table}
                ADD COLUMN IF NOT EXISTS {Columns.TIMESTAMP} BIGINT
                """)
                self.session.execute(add_timestamp_column_query)
                logger.info("Timestamp column added successfully.")
        except SQLAlchemyError as e:
            logger.error(f"Error adding timestamp column: {e}")

        self.session.commit()
        self.session.close()

    def add_author_column(self, table):
        """Add an author column to the table if it doesn't already exist."""
        try:
            with self.session.begin():
                add_author_column_query = text(f"""
                ALTER TABLE {table}
                ADD COLUMN IF NOT EXISTS {Columns.AUTHOR} TEXT
                """)
                self.session.execute(add_author_column_query)
                logger.info("Author column added successfully.")
        except SQLAlchemyError as e:
            logger.error(f"Error adding author column: {e}")

        self.session.commit()
        self.session.close()

    def update_timestamps(self, nodes_with_timestamp, table):
        """Update the timestamp values for the nodes."""
        try:
            with self.session.begin():
                update_timestamp_query = text(f"""
                UPDATE {table}
                SET {Columns.TIMESTAMP} = :timestamp
                WHERE {Columns.NODE_ID} = :node_id
                """)
                for node_id, timestamp in nodes_with_timestamp.items():
                    self.session.execute(update_timestamp_query, {'timestamp': timestamp, 'node_id': node_id})
        except SQLAlchemyError as e:
            logger.error(f"Error updating timestamp values: {e}")

        self.session.commit()
        self.session.close()
        
    def update_authors(self, nodes_with_author, table):
        """Update the author values for the nodes."""
        try:
            with self.session.begin():
                update_author_query = text(f"""
                UPDATE {table}
                SET {Columns.AUTHOR} = :author
                WHERE {Columns.NODE_ID} = :node_id
                """)
                for node_id, author in nodes_with_author.items():
                    self.session.execute(update_author_query, {'author': author, 'node_id': node_id})
        except SQLAlchemyError as e:
            logger.error(f"Error updating author values: {e}")

        self.session.commit()
        self.session.close()

    def query_post_of_author(self, table, list_authors):
        try:
            query = text(f"""
                    SELECT {Columns.TEXT}
                    FROM {table}
                    WHERE {Columns.AUTHOR} IN :authors
                    ORDER BY {Columns.TIMESTAMP} DESC
                    """)
            result = self.session.execute(query, {'authors': tuple(list_authors)})
            result = result.fetchall()
            self.session.commit()
            self.session.close()
        
            return result

        except SQLAlchemyError as e:
            logger.error(f"Error querying post of author: {e}")
            self.session.commit()
            self.session.close()
        
            return []

    def prune_vector_db_tweet(self):
        posgre_table = f"data_{PostgresRAGDBConfig.RAG_TABLE}"
        end_timestamp = int(time.time())
        start_timestamp = end_timestamp - TimeConstants.DAYS_30*3
        
        try:
            with self.session.begin():
                prune_query = text(f"""
                DELETE FROM {posgre_table}
                WHERE {Columns.TIMESTAMP} < :start_timestamp
                """)
                self.session.execute(prune_query, {'start_timestamp': start_timestamp})
        except SQLAlchemyError as e:
            logger.error(f"Error pruning tweet data: {e}")
        
        self.session.commit()
        self.session.close()

    def prune_vector_db_telegram(self):
        posgre_table = f"data_{PostgresRAGDBConfig.RAG_TABLE_V2}"
        end_timestamp = int(time.time())
        start_timestamp = end_timestamp - TimeConstants.DAYS_30*12

        try:
            with self.session.begin():
                prune_query = text(f"""
                DELETE FROM {posgre_table}
                WHERE {Columns.TIMESTAMP} < :start_timestamp
                """)
                self.session.execute(prune_query, {'start_timestamp': start_timestamp})
        except SQLAlchemyError as e:
            logger.error(f"Error pruning telegram data: {e}")

        self.session.commit()
        self.session.close()