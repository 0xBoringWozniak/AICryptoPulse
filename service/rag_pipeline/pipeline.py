import os
from typing import Dict, List

import faiss
import pandas as pd
from dotenv import load_dotenv
from langchain import hub
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

from langchain_community.vectorstores import FAISS
from langchain_gigachat import GigaChat

from config import RAG_CONFIG
from encoder_model import EmbeddingModelWrapper
from get_data_psql import get_data_from_psql


class RagPipeline:
    """
    A pipeline for handling Retrieval-Augmented Generation (RAG) workflows:
      1) Document retrieval (FAISS-based).
      2) Answering user queries via an LLM.
    """

    CONFIG_COLUMN = "DATA_TABLES"  # Key in RAG_CONFIG for table metadata
    TEXT_COLUMN = "text"  # Default column name for text data
    IDS_COLUMN = "id"  # Default column name for document IDs

    def __init__(
        self,
        index_path: str = "./faiss_index_custom_embeddings",
        model_path_or_id: str = "all-MiniLM-L6-v2",
    ):
        """
        Initializes the RAG pipeline by loading/creating a FAISS index and setting up the encoder model.

        Args:
            index_path (str): Path to the FAISS index directory.
            model_path_or_id (str): Identifier or path to the sentence-transformer model.
        """
        self._load_environment_variables()
        self.index_path = index_path
        self.encoder_model = EmbeddingModelWrapper(model_path_or_id)
        self.faiss_index = self._initialize_faiss_index()
        self.gigachat_prompt_template = hub.pull("rlm/rag-prompt")

    def _load_environment_variables(self):
        """Load environment variables from .env file."""
        load_dotenv()

    def _initialize_faiss_index(self) -> FAISS:
        """
        Loads a FAISS index from disk if available, otherwise builds a new index.

        Returns:
            FAISS: A LangChain FAISS vector store instance.
        """
        if self.index_path and os.path.isdir(self.index_path):
            return FAISS.load_local(
                self.index_path,
                self.encoder_model,
                allow_dangerous_deserialization=True,  # need to think about it
            )
        return self._build_faiss_index()

    def _get_filtered_data(
        self, raw_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, List[str]]:
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

    def _build_faiss_index(self) -> FAISS:
        """
        Builds a new FAISS index from the data fetched from PostgreSQL.

        Returns:
            FAISS: A LangChain FAISS vector store instance.
        """
        raw_data = get_data_from_psql()
        filtered = self._get_filtered_data(raw_data)
        split_docs = self._split_documents(filtered["docs"])

        faiss_store = FAISS.from_documents(split_docs, self.encoder_model)
        faiss_store.save_local(self.index_path)
        return faiss_store

    def _generate_answer_openai(self, user_prompt: str, context: str) -> str:
        """
        Generates an answer using OpenAI's model, given the user prompt and retrieved context.

        Args:
            user_prompt (str): The question from the user.
            context (str): Relevant context from the FAISS index.

        Returns:
            str: The generated answer.
        """
        llm = OpenAI(openai_api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7)
        prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=("Context:\n{context}\n\n" "Question: {question}\n" "Answer:"),
        )
        chain = load_qa_chain(llm, chain_type="stuff", prompt=prompt)
        return chain.run({"context": context, "question": user_prompt})

    def _generate_answer_gigachat(self, user_prompt: str, context: str) -> str:
        """
        Generates an answer using GigaChat, given the user prompt and retrieved context.

        Args:
            user_prompt (str): The question from the user.
            context (str): Relevant context from the FAISS index.

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
        Executes the main RAG pipeline for a user query:
          1) Retrieve top matching documents from the FAISS index.
          2) Generate an answer from the selected context using GigaChat (by default).

        Args:
            user_prompt (str): The query from the user.

        Returns:
            str: The generated answer.
        """
        results = self.faiss_index.similarity_search_with_score(user_prompt, k=5)
        context = "\n".join([doc.page_content for doc, _score in results])
        return self._generate_answer_gigachat(user_prompt, context)
