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
                                table_name=PostgresRAGDBConfig.RAG_TABLE,
                                embed_dim=int(EmbeddingModelConfig.EMBEDDING_DIMENSION)
                                )
        self.engine = create_engine(connection_url)
        self.session = Session(bind=self.engine)
        self.embedding_model = EmbeddingModel()
        if self.table_exists(f'data_{PostgresRAGDBConfig.RAG_TABLE}'):
            self.ensure_unique_constraint()

    def table_exists(self, table_name):
        """Check if a table exists in the database."""
        inspector = inspect(self.engine)
        return inspector.has_table(table_name)

    def ensure_unique_constraint(self):
        """Ensure the node_id column has a unique constraint."""
        try:
            check_constraint_query = text(f"""
            SELECT conname
            FROM pg_constraint
            WHERE conname = '{Columns.NODE_ID}'
            """)
            result = self.session.execute(check_constraint_query).fetchone()
            print(result)

            if not result:
                alter_query = text(f"""
                ALTER TABLE data_{PostgresRAGDBConfig.RAG_TABLE}
                ADD CONSTRAINT {Columns.NODE_ID} UNIQUE ({Columns.NODE_ID})
                """)
                self.session.execute(alter_query)
                self.session.commit()
                logger.info("Unique constraint on node_id added successfully.")
            else:
                logger.info("Unique constraint on node_id already exists.")
        except SQLAlchemyError as e:
            logger.error(f"Error ensuring unique constraint on node_id: {e}")
            self.session.rollback()
        finally:
            self.session.close()

    # update database, if a node with the same id exists, update it
    def upsert_nodes(self, nodes):
        if not self.table_exists(f'data_{PostgresRAGDBConfig.RAG_TABLE}'):
            self.vetor_store.add(nodes)
        else:
            """Upsert a list of nodes into the database. If the node_id exists, overwrite the existing entry."""
            try:
                # Prepare the insert query with ON CONFLICT clause
                insert_query = text(f"""
                INSERT INTO data_{PostgresRAGDBConfig.RAG_TABLE} ({Columns.TEXT}, {Columns.METADATA}, {Columns.NODE_ID}, {Columns.EMBEDDING})
                VALUES (:text, :metadata_, :node_id, :embedding)
                ON CONFLICT ({Columns.NODE_ID}) DO UPDATE
                SET {Columns.TEXT} = EXCLUDED.{Columns.TEXT},
                    {Columns.METADATA} = EXCLUDED.{Columns.METADATA},
                    {Columns.EMBEDDING} = EXCLUDED.{Columns.EMBEDDING}
                """)

                # Prepare the list of dictionaries for each node
                values_to_insert = []
                for node in nodes:
                    metadata_json = json.dumps(node.metadata)
                    values_to_insert.append({
                        'text': node.text,
                        'metadata_': metadata_json,
                        'node_id': node.id_,
                        'embedding': node.embedding
                    })

                # Execute the query with multiple values
                # Log the percentage of nodes upserted at every 10% increment
                chunk_size = max(1, len(values_to_insert) // 10)  # Ensure chunk_size is at least 1
                for i in range(0, len(values_to_insert), chunk_size):
                    self.session.execute(insert_query, values_to_insert[i:i + chunk_size])
                    self.session.commit()
                    percentage_done = (i // chunk_size + 1) * 10
                    logger.info(f"Upserted {percentage_done}% of nodes.")

            except SQLAlchemyError as e:
                logger.error(f"Error upserting nodes: {e}")
                self.session.rollback()
            finally:
                self.session.close()

                
