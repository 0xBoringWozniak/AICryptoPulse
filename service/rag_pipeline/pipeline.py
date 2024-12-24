from config import RAG_CONFIG
from encoder_model import EmbeddingModelWrapper
from get_data_psql import get_data_from_psql

import os
from typing import Dict

import faiss
import pandas as pd

from langchain import hub
from langchain.docstore.document import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain_gigachat import GigaChat
from langchain.text_splitter import RecursiveCharacterTextSplitter


class RagPipeline:
    """
    A pipeline for handling retrieval-augmented generation (RAG) workflows.
    This includes document retrieval via FAISS and answering user queries using a language model.
    """

    CONFIG_COLUMN = "DATA_TABLES"  # Configuration key for accessing table metadata
    TEXT_COLUMN = "text"  # Default column name for text data
    IDS_COLUMN = "id"  # Default column name for document IDs

    def __init__(
        self,
        index_path: str = "./faiss_index_custom_embeddings",
        model_path_or_id: str = "all-MiniLM-L6-v2",
        **model_kwargs
    ):
        """
        Initializes the RAG pipeline by loading or creating a FAISS index and initializing the encoder model.

        Args:
            index_path (str): Path to the FAISS index file.
            model_path_or_id (str): Identifier or path to the sentence transformer model.
        """
        self.index_path = index_path
        self.encoder_model = EmbeddingModelWrapper(model_path_or_id)
        self.faiss_index = self._initialize_faiss_index()
        self.gigachat_prompt_template = hub.pull("rlm/rag-prompt")

    def _initialize_faiss_index(self):
        """
        Initializes the FAISS index by loading it from disk if it exists, otherwise builds a new index.

        Returns:
            faiss.Index: The initialized FAISS index.
        """
        if self.index_path and os.path.isfile(self.index_path):
            return faiss.read_index(self.index_path)
        return self._build_index()

    def _get_filtered_data(self, raw_data: Dict[str, pd.DataFrame]) -> Dict[str, list]:
        """
        Filters raw data to extract documents and their corresponding IDs.

        Args:
            raw_data (Dict[str, pd.DataFrame]): Raw data fetched from the database.

        Returns:
            Dict[str, list]: A dictionary containing document texts and their IDs.
        """
        docs, docs_ids = [], []
        for table_name, data in raw_data.items():
            config = RAG_CONFIG[self.CONFIG_COLUMN][table_name]
            docs_ids.extend(data[config[self.IDS_COLUMN]].tolist())
            docs.extend(data[config[self.TEXT_COLUMN]].tolist())
        return {"docs_ids": docs_ids, "docs": docs}

    def _split_documents(self, documents: list) -> list:
        """
        Splits documents into smaller chunks using an efficient text splitter.

        Args:
            documents (list): List of document strings to split.

        Returns:
            list: List of split document chunks.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=64,
        )
        documents_processed = [
            Document(page_content=text) for text in documents if text is not None
        ]
        split_docs = text_splitter.split_documents(documents_processed)
        return split_docs

    def _build_index(self):
        """
        Builds a FAISS index from the data fetched from the PostgreSQL database.

        Returns:
            FAISS: The created FAISS index object.
        """
        raw_data = get_data_from_psql()
        filtered_docs = self._get_filtered_data(raw_data)
        split_docs = self._split_documents(filtered_docs["docs"])
        faiss_index = FAISS.from_documents(split_docs, self.encoder_model)
        faiss_index.save_local(self.index_path)
        return faiss_index

    def _generate_answer_openai(self, user_prompt: str, context: str) -> str:
        """
        Generates an answer to the user query using a language model based on the provided context.

        Args:
            user_prompt (str): The user query.
            context (str): The context retrieved from the FAISS index.

        Returns:
            str: The generated answer.
        """
        llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)
        qa_prompt = PromptTemplate(
            input_variables=[
                "context",
                "question",
            ],
            template="""
                Context:
                {context}

                Question: {question}
                Answer:
            """.strip(),
        )
        qa_chain = load_qa_chain(llm, chain_type="stuff", prompt=qa_prompt)
        return qa_chain.run({"context": context, "question": user_prompt})

    def _generate_answer_gigachat(self, user_prompt: str, context: str) -> str:
        """
        Generates an answer to the user query using a language model based on the provided context.

        Args:
            user_prompt (str): The user query.
            context (str): The context retrieved from the FAISS index.

        Returns:
            str: The generated answer.
        """
        llm = GigaChat(verify_ssl_certs=False, scope="GIGACHAT_API_PERS")
        prompt = self.gigachat_prompt_template.invoke(
            {"question": user_prompt, "context": context}
        )
        return llm.invoke(prompt)

    def run(self, user_prompt: str) -> str:
        """
        Executes the main pipeline for answering user queries.

        Args:
            user_prompt (str): The query provided by the user.

        Returns:
            str: The generated answer based on retrieved documents.
        """
        results = self.faiss_index.similarity_search_with_score(user_prompt, k=5)
        context = "\n".join([result[0].page_content for result in results])
        return self._generate_answer_gigachat(user_prompt, context)
