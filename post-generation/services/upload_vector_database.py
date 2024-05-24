import json
import os
import pandas as pd 
from multithread_processing.base_job import BaseJob
from utils.logger_utils import get_logger, write_file

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text 

from databases.postgresql import PostgresDB
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.utils import node_to_metadata_dict
from utils.preprocess_utils import get_lemma

Session = sessionmaker()

class Columns:
    ID = 'id'
    TEXT = 'text'
    METADATA = 'metadata_'
    NODE_ID = 'node_id'
    EMBEDDING = 'embedding'
    TIMESTAMP = 'timestamp'

class UploadVectorDB(BaseJob):
    def __init__(self, embed_model, importer, exporter, index_lst, df_tweet_filter, interval=None, end_timestamp=None, retry=True, max_workers=4, batch_size=500):
        self.embed_model = embed_model
        self.importer = importer
        self.exporter = exporter
        self.interval = interval
        self.df_tweet_filter = df_tweet_filter
        self.batch_size = batch_size
        super().__init__(work_iterable=index_lst, max_workers=max_workers, batch_size=batch_size)

    def _execute_batch(self, works):
        logg = get_logger('UploadVectorDB')
        nodes = []
        nodes_with_timestamp = {}
        
        for work in works:
            df = self.df_tweet_filter[work-self.batch_size:work]
            for index, row in df.iterrows():
                node = TextNode(text=row['content'], id_=f"{row['authorName']}_{row['_id']}", )
                nodes.append(node)
                nodes_with_timestamp[node.id_] = row['timestamp']

        for node in nodes:
            node_embedding = self.embed_model._embed_model.get_text_embedding(
                get_lemma(node.get_content(metadata_mode="all"))
            )
            node.embedding = node_embedding
            node.metadata = node_to_metadata_dict(node)

        logg.info("Successfully process tweet data ...")
        logg.info("Start to upload tweet data ...")

        logg.info(f"Uploading {len(nodes_with_timestamp)} nodes to the database ...")

        if not self.importer.table_exists(self.exporter):
            self.importer.vector_store.add(nodes)
            try:
                self.importer.ensure_unique_constraint()
            except:
                pass

            self.importer.add_timestamp_column()
            self.importer.update_timestamps(nodes_with_timestamp)
        
        try:
            self.importer.ensure_unique_constraint()
        except:
            pass

        # Prepare the insert query with ON CONFLICT clause
        insert_query = text(f"""
        INSERT INTO {self.exporter} ({Columns.TEXT}, {Columns.METADATA}, {Columns.NODE_ID}, {Columns.EMBEDDING}, {Columns.TIMESTAMP})
        VALUES (:text, :metadata_, :node_id, :embedding, :timestamp)
        ON CONFLICT ({Columns.NODE_ID}) DO UPDATE
        SET {Columns.TEXT} = EXCLUDED.{Columns.TEXT},
            {Columns.METADATA} = EXCLUDED.{Columns.METADATA},
            {Columns.EMBEDDING} = EXCLUDED.{Columns.EMBEDDING},
            {Columns.TIMESTAMP} = EXCLUDED.{Columns.TIMESTAMP}
        """)

        for work in works:
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

            # Divide the list of dictionaries into batches
            for value in values_to_insert[work-self.batch_size:work]:
                with self.importer.session.begin(): 
                    try:
                        self.importer.session.execute(insert_query, value)
                    except SQLAlchemyError as e:
                        logg.error(f"Error upserting nodes: {e}")

    def _end(self):
        self.batch_executor.shutdown()
    
