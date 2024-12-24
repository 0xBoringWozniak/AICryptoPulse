from typing import Dict, List
from datetime import datetime, timedelta
from io import BytesIO

import tempfile
import boto3
import faiss
import pandas as pd
import sqlalchemy

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from sentence_transformers import SentenceTransformer


class EmbeddingModelWrapper:
    """
    Wrapper class for SentenceTransformer model
    """
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)

    def __call__(self, text):
        return self.model.encode([text])[0].tolist()

    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()


RAG_CONFIG = {
    "DATA_TABLES": {
        "dl_feed_news": {"id": "guid", "text": "content"},
        "dl_feed_tweets": {"id": "tweet_id", "text": "tweet"},
    },
}


class IndexPipeline:
    """
    A pipeline for building and managing FAISS indexes for document retrieval.
    """

    CONFIG_COLUMN = "DATA_TABLES"  # Key in RAG_CONFIG for table metadata
    TEXT_COLUMN = "text"  # Default column name for text data
    IDS_COLUMN = "id"  # Default column name for document IDs

    def __init__(self, db_engine: sqlalchemy.engine.Engine, s3_client, model_path_or_id: str = "all-MiniLM-L6-v2"):
        """
        Initializes the RAG pipeline by loading/creating a FAISS index and setting up the encoder model.

        Args:
            model_path_or_id (str): Identifier or path to the sentence-transformer model.
        """
        self.encoder_model = EmbeddingModelWrapper(model_path_or_id)
        self.db_engine = db_engine
        self.s3_client = s3_client

    def _load_data(
        self, from_date: datetime = datetime.now() - timedelta(days=30),
    ) -> Dict[str, pd.DataFrame]:
        data_tables = {}
        tables_name = RAG_CONFIG["DATA_TABLES"]
        time_filters = {
            'dl_feed_news': 'pub_date',
            'dl_feed_tweets': 'tweet_created_at'
        }
        for table_name in tables_name.keys():
            query = table_name
            if table_name in time_filters:
                query += f" WHERE {time_filters[table_name]} >= '{from_date}'"
            db_data = pd.read_sql(f"SELECT * FROM {query}", self.db_engine)
            data_tables[table_name] = db_data
        return data_tables

    def _save_faiss_index_to_s3(self, faiss_index: FAISS, bucket_name: str, object_key: str):
        """
        Saves the FAISS index to AWS S3 with a dynamic filename based on `from_date`.

        Args:
            bucket_name (str): The S3 bucket name.
            object_key (str): The object key for the index file.
        """
        object_key = f"llama_feed_index_{object_key}"

        # Use a temporary file to store the FAISS index
        with tempfile.NamedTemporaryFile() as temp_file:
            faiss.write_index(faiss_index.index, temp_file.name)
            temp_file.seek(0)

            # Upload the file to S3
            self.s3_client.upload_file(temp_file.name, bucket_name, object_key)

    def _get_filtered_data(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
        """
        Filters raw data to extract document texts and IDs based on configuration.

        Args:
            raw_data (Dict[str, pd.DataFrame]): Raw data from the database.

        Returns:
            Dict[str, List[str]]: A dictionary with two keys:
                                  "docs_ids" -> list of doc IDs,
                                  "docs" -> list of doc texts.
        """
        all_docs, all_doc_ids = [], []
        for table_name, df in raw_data.items():
            config = RAG_CONFIG[self.CONFIG_COLUMN][table_name]
            ids_column = config[self.IDS_COLUMN]
            text_column = config[self.TEXT_COLUMN]
            all_doc_ids.extend(df[ids_column].astype(str).tolist())
            all_docs.extend(df[text_column].astype(str).tolist())
        return {"docs_ids": all_doc_ids, "docs": all_docs}

    def _split_documents(self, documents: List[str]) -> List[Document]:
        """
        Splits raw text documents into smaller chunks using a character-based splitter.

        Args:
            documents (List[str]): A list of document strings.

        Returns:
            List[Document]: Split documents as LangChain Document objects.
        """
        splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
        docs_as_objs = [Document(page_content=text) for text in documents if text]
        return splitter.split_documents(docs_as_objs)

    def _build_faiss_index(self, raw_data: Dict[str, pd.DataFrame]) -> FAISS:
        """
        Builds a new FAISS index from the data fetched from PostgreSQL.

        Returns:
            FAISS: A LangChain FAISS vector store instance.
        """
        filtered = self._get_filtered_data(raw_data)
        split_docs = self._split_documents(filtered["docs"])
        faiss_store = FAISS.from_documents(split_docs, self.encoder_model)
        return faiss_store

    def run(self, from_date: datetime = datetime.now() - timedelta(days=30)):
        data: Dict[str, pd.DataFrame] = self._load_data(from_date=from_date)
        faiss_index = self._build_faiss_index(data)
        name = f"llama_feed_index_{from_date.strftime('%Y-%m-%d')}-{datetime.now().strftime('%Y-%m-%d')}"
        self._save_faiss_index_to_s3(faiss_index, "ai-embeddings-bucket", name)
