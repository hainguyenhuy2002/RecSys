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
from config import PostgresRAGDBConfig, EmbeddingModelConfig
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
    AUTHOR = 'author'

class UploadVectorDB(BaseJob):
    def __init__(self, embed_model, importer, exporter, index_lst, df_filter, interval=None, end_timestamp=None, retry=True, max_workers=4, batch_size=500, social=None):
        self.embed_model = embed_model
        self.importer = importer
        self.exporter = exporter
        self.interval = interval
        self.df_filter = df_filter
        self.batch_size = batch_size
        self.social = social
        super().__init__(work_iterable=index_lst, max_workers=max_workers, batch_size=batch_size)

    def _execute_batch(self, works):
        logg = get_logger('UploadVectorDB')
        nodes = []
        nodes_with_timestamp = {}
        nodes_with_author = {}
        
        if self.social == 'twitter':
            for work in works:
                df = self.df_filter[work-self.batch_size:work]
                for index, row in df.iterrows():
                    node = TextNode(text=row['content'], id_=f"{row['authorName']}_{row['_id']}", )
                    nodes.append(node)
                    nodes_with_timestamp[node.id_] = row['timestamp']
                    nodes_with_author[node.id_] = row['authorName']

        elif self.social == 'telegram':
            for work in works:
                df = self.df_filter[work-self.batch_size:work]
                for index, row in df.iterrows():
                    node = TextNode(text=row['content'], id_=f"{row['_id']}", )
                    nodes.append(node)
                    nodes_with_timestamp[node.id_] = row['timestamp']
                    nodes_with_author[node.id_] = row['_id'].split('_')[0]

        for node in nodes:
            node_embedding = self.embed_model._embed_model.get_text_embedding(
                get_lemma(node.get_content(metadata_mode="all"))
            )
            node.embedding = node_embedding
            node.metadata = node_to_metadata_dict(node)

        nodes = list({node.id_: node for node in nodes}.values())

        logg.info("Successfully process data ...")
        logg.info("Start to upload data ...")

        logg.info(f"Uploading {len(nodes)} nodes to the database ...")

        if self.social == 'twitter':
            table = f"data_{PostgresRAGDBConfig.RAG_TABLE}"
            if not self.importer.table_exists(self.exporter):
                self.importer.vector_store.add(nodes)
                self.importer.ensure_unique_constraint(table)

                self.importer.add_timestamp_column(table)
                self.importer.update_timestamps(nodes_with_timestamp, table)
                self.importer.add_author_column(table)
                self.importer.update_authors(nodes_with_author, table)

            elif self.importer.table_exists(self.exporter):
                try:
                    self.importer.ensure_unique_constraint(table)
                except:
                    pass

                # self.importer.add_author_column()
                
                # Prepare the insert query with ON CONFLICT clause
                insert_query = text(f"""
                INSERT INTO {self.exporter} ({Columns.TEXT}, {Columns.METADATA}, {Columns.NODE_ID}, {Columns.EMBEDDING}, {Columns.TIMESTAMP}, {Columns.AUTHOR})
                VALUES (:text, :metadata_, :node_id, :embedding, :timestamp, :author)
                ON CONFLICT ({Columns.NODE_ID}) DO UPDATE
                SET {Columns.TEXT} = EXCLUDED.{Columns.TEXT},
                    {Columns.METADATA} = EXCLUDED.{Columns.METADATA},
                    {Columns.EMBEDDING} = EXCLUDED.{Columns.EMBEDDING},
                    {Columns.TIMESTAMP} = EXCLUDED.{Columns.TIMESTAMP},
                    {Columns.AUTHOR} = EXCLUDED.{Columns.AUTHOR}
                """)

                for work in works:
                    # Prepare the list of dictionaries for each node
                    values_to_insert = []
                    for node in nodes:
                        metadata_json = json.dumps(node.metadata)
                        timestamp = nodes_with_timestamp[node.id_]
                        author = node.id_.split('_')[0]
                        values_to_insert.append({
                            'text': node.text,
                            'metadata_': metadata_json,
                            'node_id': node.id_,
                            'embedding': node.embedding,
                            'timestamp': timestamp,
                            'author': author
                        })

                    # Divide the list of dictionaries into batches
                    for value in values_to_insert[work-self.batch_size:work]:
                        with self.importer.session.begin(): 
                            try:
                                self.importer.session.execute(insert_query, value)
                            except SQLAlchemyError as e:
                                logg.error(f"Error upserting nodes: {e}")

        elif self.social == 'telegram':
            table = f"data_{PostgresRAGDBConfig.RAG_TABLE_V2}"
            if not self.importer.table_exists(self.exporter):
                self.importer.vector_store_v2.add(nodes)
                self.importer.ensure_unique_constraint(table)

                self.importer.add_timestamp_column(table)
                self.importer.update_timestamps(nodes_with_timestamp, table)
                self.importer.add_author_column(table)
                self.importer.update_authors(nodes_with_author, table)

            elif self.importer.table_exists(self.exporter):
                try:
                    self.importer.ensure_unique_constraint(table)
                except:
                    pass

                # self.importer.add_author_column()
                
                # Prepare the insert query with ON CONFLICT clause
                insert_query = text(f"""
                INSERT INTO {self.exporter} ({Columns.TEXT}, {Columns.METADATA}, {Columns.NODE_ID}, {Columns.EMBEDDING}, {Columns.TIMESTAMP}, {Columns.AUTHOR})
                VALUES (:text, :metadata_, :node_id, :embedding, :timestamp, :author)
                ON CONFLICT ({Columns.NODE_ID}) DO UPDATE
                SET {Columns.TEXT} = EXCLUDED.{Columns.TEXT},
                    {Columns.METADATA} = EXCLUDED.{Columns.METADATA},
                    {Columns.EMBEDDING} = EXCLUDED.{Columns.EMBEDDING},
                    {Columns.TIMESTAMP} = EXCLUDED.{Columns.TIMESTAMP},
                    {Columns.AUTHOR} = EXCLUDED.{Columns.AUTHOR}
                """)

                for work in works:
                    # Prepare the list of dictionaries for each node
                    values_to_insert = []
                    for node in nodes:
                        metadata_json = json.dumps(node.metadata)
                        timestamp = nodes_with_timestamp[node.id_]
                        author = node.id_.split('_')[0]
                        values_to_insert.append({
                            'text': node.text,
                            'metadata_': metadata_json,
                            'node_id': node.id_,
                            'embedding': node.embedding,
                            'timestamp': timestamp,
                            'author': author
                        })

                    # Divide the list of dictionaries into batches
                    for value in values_to_insert[work-self.batch_size:work]:
                        with self.importer.session.begin(): 
                            try:
                                self.importer.session.execute(insert_query, value)
                            except SQLAlchemyError as e:
                                logg.error(f"Error upserting nodes: {e}")

            
            # # Với những hàng có author rỗng thì cập nhật lại author từ node_id
            # update_author_query = text(f"""
            # UPDATE {self.exporter}
            # SET {Columns.AUTHOR} = :author
            # WHERE {Columns.NODE_ID} = :node_id
            # """)
            # select_all_data_query = text(f"""                          
            # SELECT * FROM {self.exporter}
            # """)

            # # Kiểm tra xem author có rỗng không
            # with self.importer.session.begin():
            #     result = self.importer.session.execute(select_all_data_query)
            #     results = result.fetchall()
            #     for row in results:
            #         if row[6] is None:
            #             author = '_'.join(row[3].split('_')[:-1])
            #             self.importer.session.execute(update_author_query, {'author': author, 'node_id': row[3]})

    def _end(self):
        self.batch_executor.shutdown()
    
