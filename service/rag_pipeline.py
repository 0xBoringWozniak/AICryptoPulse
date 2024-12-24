import os
import pickle
import tempfile

import faiss
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer

from service.creds import OPENAI_API_KEY

RAG_CONFIG = {
    'OPENAI_MODEL': 'gpt-4o',
    'EMBEDDING_MODEL': 'all-MiniLM-L6-v2',
    'TEMPERATURE': 0.6,
}


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


class RagPipeline:
    """
    A pipeline for handling Retrieval-Augmented Generation (RAG) workflows:
      1) Document retrieval (FAISS-based).
      2) Answering user queries via an LLM.
    """

    def __init__(self):
        """
        Initializes the RAG pipeline by loading/creating a FAISS index and setting up the encoder model.

        Args:
            index_path (str): Path to the FAISS index directory.
            model_path_or_id (str): Identifier or path to the sentence-transformer model.
        """
        self.encoder_model = EmbeddingModelWrapper(RAG_CONFIG["EMBEDDING_MODEL"])
        self.faiss_index = None

    def initialize_faiss_index(self, s3_client, bucket_name: str, object_key: str):
        """
        Loads a FAISS index, `docstore`, and `index_to_docstore_id` from S3.

        Args:
            s3_client (boto3.client): The S3 client object.
            bucket_name (str): The S3 bucket name.
            object_key (str): The object key for the index file in S3.
        """
        with tempfile.NamedTemporaryFile(delete=True) as temp_index_file, \
            tempfile.NamedTemporaryFile(delete=True) as temp_meta_file:
            
            # Download FAISS index
            s3_client.download_file(bucket_name, f"{object_key}_index", temp_index_file.name)
            raw_faiss_index = faiss.read_index(temp_index_file.name)
            
            # Download metadata
            s3_client.download_file(bucket_name, f"{object_key}_meta", temp_meta_file.name)
            with open(temp_meta_file.name, "rb") as meta_file:
                metadata = pickle.load(meta_file)

            self.faiss_index = FAISS(
                embedding_function=self.encoder_model,
                index=raw_faiss_index,
                docstore=metadata["docstore"],
                index_to_docstore_id=metadata["index_to_docstore_id"],
            )

    def run(self, user_prompt: str) -> str:
        """
        Executes the main RAG pipeline for a user query:
          1) Retrieve top matching documents from the FAISS index.
          2) Generate an answer from the selected context using OpenAI.

        Args:
            user_prompt (str): The query from the user.

        Returns:
            str: The generated answer.
        """
        if self.faiss_index is None:
            raise ValueError("FAISS index is not initialized. Run initialize_faiss_index first.")

        results = self.faiss_index.similarity_search_with_score(user_prompt, k=5)
        input_documents = [doc for doc, _score in results]
        if not input_documents:
            raise ValueError("No matching documents found in the FAISS index.")
        chain = load_qa_chain(
            OpenAI(openai_api_key=OPENAI_API_KEY, temperature=RAG_CONFIG["TEMPERATURE"]),
            chain_type="stuff",
        )
        return chain.run({"input_documents": input_documents, "question": user_prompt})
