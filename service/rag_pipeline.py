import pickle
import tempfile

import faiss
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer

from service.creds import OPENAI_API_KEY

RAG_CONFIG = {
    "OPENAI_MODEL": "gpt-4o",
    "EMBEDDING_MODEL": "all-MiniLM-L6-v2",
    "TEMPERATURE": 0.6,
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

    def __init__(self, nof_retrieved_docs: int = 3, nof_messages_to_store: int = 15):
        """
        Initializes the RAG pipeline by loading/creating a FAISS index and setting up the encoder model.

        Args:
            nof_retrieved_docs (int): number of documents for augmentation user query.
        """
        # TODO: add db
        set_llm_cache(SQLiteCache(database_path=".langchain.db"))

        self.nof_retrieved_docs = nof_retrieved_docs
        self.encoder_model = EmbeddingModelWrapper(RAG_CONFIG["EMBEDDING_MODEL"])
        self.memory = ConversationBufferWindowMemory(
            k=nof_messages_to_store, memory_key="chat_history", return_messages=True
        )

        self.prompt_template = PromptTemplate(
            input_variables=["chat_history", "question"],
            template=(
                "The following is a conversation between a user and an assistant. The assistant is helpful, "
                "knowledgeable, and provides concise answers.\n\n"
                "The user has the following interests:\n"
                "{system_prompt}\n"
                "Documents:\n"
                "{input_documents}\n"  # retrieved docs
                "Chat history:\n"
                "{chat_history}\n\n"  # memory
                "User: {question}\n"  # main query
                "Assistant:"
            ),
        )
        self.decoder = OpenAI(
            model=RAG_CONFIG["OPENAI_MODEL"],
            openai_api_key=OPENAI_API_KEY,
            temperature=RAG_CONFIG["TEMPERATURE"],
        )
        self.chain = load_qa_chain(
            chain_type="stuff",
            memory=self.memory,
            prompt=self.prompt_template,
        )
        self.faiss_index = None

    def initialize_faiss_index(self, s3_client, bucket_name: str, object_key: str):
        """
        Loads a FAISS index, `docstore`, and `index_to_docstore_id` from S3.

        Args:
            s3_client (boto3.client): The S3 client object.
            bucket_name (str): The S3 bucket name.
            object_key (str): The object key for the index file in S3.
        """
        with tempfile.NamedTemporaryFile(
            delete=True
        ) as temp_index_file, tempfile.NamedTemporaryFile(
            delete=True
        ) as temp_meta_file:

            # Download FAISS index
            s3_client.download_file(
                bucket_name, f"{object_key}_index", temp_index_file.name
            )
            raw_faiss_index = faiss.read_index(temp_index_file.name)

            # Download metadata
            s3_client.download_file(
                bucket_name, f"{object_key}_meta", temp_meta_file.name
            )
            with open(temp_meta_file.name, "rb") as meta_file:
                metadata = pickle.load(meta_file)

            self.faiss_index = FAISS(
                embedding_function=self.encoder_model,
                index=raw_faiss_index,
                docstore=metadata["docstore"],
                index_to_docstore_id=metadata["index_to_docstore_id"],
            )

    def run(self, user_prompt: dict[str, str]) -> str:
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
            raise ValueError(
                "FAISS index is not initialized. Run initialize_faiss_index first."
            )

        results = self.faiss_index.similarity_search_with_score(
            user_prompt, k=self.nof_retrieved_docs
        )
        input_documents = [doc for doc, _score in results]
        if not input_documents:
            raise ValueError("No matching documents found in the FAISS index.")

        response = self.chain.run(
            {
                "input_documents": input_documents,
                "question": user_prompt["prompt"],
                "system_prompt": user_prompt["system_prompt"],
                "chat_history": self.memory.load_memory_variables({})["chat_history"],
            }
        )

        self.memory.save_context(
            {"User": user_prompt["prompt"]}, {"Assistant": response}
        )
        return response
