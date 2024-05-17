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

import json

logger = get_logger('PostgreSQL thread safe')
Session = sessionmaker()

class Columns:
    ID = 'id'
    TEXT = 'text'
    METADATA = 'metadata_'
    NODE_ID = 'node_id'
    EMBEDDING = 'embedding'
    TIMESTAMP = 'timestamp'


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
        self.engine = create_engine(connection_url)
        self.session = Session(bind=self.engine)
        self.embedding_model = EmbeddingModel()

    def table_exists(self, table_name):
        """Check if a table exists in the database."""
        inspector = inspect(self.engine)
        return inspector.has_table(table_name)

    def ensure_unique_constraint(self):
        """Ensure the node_id column has a unique constraint."""
        with self.session.begin():
            alter_query = text(f"""
            ALTER TABLE data_{PostgresRAGDBConfig.RAG_TABLE}
            ADD CONSTRAINT {PostgresRAGDBConfig.RAG_TABLE}_node_id UNIQUE ({Columns.NODE_ID})
            """)
            self.session.execute(alter_query)
            logger.info("Unique constraint on node_id added successfully.")

    def add_timestamp_column(self):
        """Add a timestamp column to the table if it doesn't already exist."""
        try:
            with self.session.begin():
                add_timestamp_column_query = text(f"""
                ALTER TABLE data_{PostgresRAGDBConfig.RAG_TABLE}
                ADD COLUMN IF NOT EXISTS {Columns.TIMESTAMP} BIGINT
                """)
                self.session.execute(add_timestamp_column_query)
                logger.info("Timestamp column added successfully.")
        except SQLAlchemyError as e:
            logger.error(f"Error adding timestamp column: {e}")

    def update_timestamps(self, nodes_with_timestamp):
        """Update the timestamp values for the nodes."""
        try:
            with self.session.begin():
                update_timestamp_query = text(f"""
                UPDATE data_{PostgresRAGDBConfig.RAG_TABLE}
                SET {Columns.TIMESTAMP} = :timestamp
                WHERE {Columns.NODE_ID} = :node_id
                """)
                for node_id, timestamp in nodes_with_timestamp.items():
                    self.session.execute(update_timestamp_query, {'timestamp': timestamp, 'node_id': node_id})
        except SQLAlchemyError as e:
            logger.error(f"Error updating timestamp values: {e}")

    def upsert_nodes(self, nodes, nodes_with_timestamp):
        if not self.table_exists(f'data_{PostgresRAGDBConfig.RAG_TABLE}'):
            self.vector_store.add(nodes)
            try:
                self.ensure_unique_constraint()
            except SQLAlchemyError as e:
                logger.error(f"Error ensuring unique constraint: {e}")

            self.add_timestamp_column()
            self.update_timestamps(nodes_with_timestamp)
        else:
            """Upsert a list of nodes into the database. If the node_id exists, overwrite the existing entry."""
            try:
                self.ensure_unique_constraint()
            except SQLAlchemyError as e:
                logger.error(f"Error ensuring unique constraint: {e}")

            try:
                # Prepare the insert query with ON CONFLICT clause
                insert_query = text(f"""
                INSERT INTO data_{PostgresRAGDBConfig.RAG_TABLE} ({Columns.TEXT}, {Columns.METADATA}, {Columns.NODE_ID}, {Columns.EMBEDDING}, {Columns.TIMESTAMP})
                VALUES (:text, :metadata_, :node_id, :embedding, :timestamp)
                ON CONFLICT ({Columns.NODE_ID}) DO UPDATE
                SET {Columns.TEXT} = EXCLUDED.{Columns.TEXT},
                    {Columns.METADATA} = EXCLUDED.{Columns.METADATA},
                    {Columns.EMBEDDING} = EXCLUDED.{Columns.EMBEDDING},
                    {Columns.TIMESTAMP} = EXCLUDED.{Columns.TIMESTAMP}
                """)

                # Prepare the list of dictionaries for each node
                values_to_insert = []
                for node in nodes:
                    metadata_json = json.dumps(node.metadata)
                    timestamp = nodes_with_timestamp[node.id_]
                    values_to_insert.append({
                        'text': node.text,
                        'metadata_': metadata_json,
                        'node_id': node.id_,
                        'embedding': node.embedding,
                        'timestamp': timestamp
                    })

                # Execute the query with multiple values
                # Log the percentage of nodes upserted at every 10% increment
                chunk_size = max(1, len(values_to_insert) // 10)  # Ensure chunk_size is at least 1
                for i in range(0, len(values_to_insert), chunk_size):
                    with self.session.begin():
                        self.session.execute(insert_query, values_to_insert[i:i + chunk_size])

                        # Log 10% increments
                        percentage_done = round((i + chunk_size) / len(values_to_insert) * 100)
                        logger.info(f"Upserted {percentage_done}% of nodes.")

            except SQLAlchemyError as e:
                logger.error(f"Error upserting nodes: {e}")
