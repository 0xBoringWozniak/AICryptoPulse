from sentence_transformers import SentenceTransformer


class EmbeddingModelWrapper:
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)

    def __call__(self, text):
        return self.model.encode([text])[0].tolist()

    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()
