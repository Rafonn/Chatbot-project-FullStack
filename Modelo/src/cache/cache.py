from langchain_core.embeddings import Embeddings
from typing import Optional, List

class ManualCachedEmbedder(Embeddings):

    def __init__(self, base_embedder: Embeddings):
        self.base_embedder = base_embedder
        self.cache = {}

    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        return self.cache.get(text)

    def _add_to_cache(self, text: str, embedding: List[float]):
        self.cache[text] = embedding

    def embed_query(self, text: str) -> List[float]:
        cached_embedding = self._get_from_cache(text)
        
        if cached_embedding is not None:
            return cached_embedding
        
        embedding = self.base_embedder.embed_query(text)
        self._add_to_cache(text, embedding)
        return embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:

        embeddings = []
        texts_to_embed = []
        for text in texts:
            cached_embedding = self._get_from_cache(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                texts_to_embed.append(text)
                embeddings.append(None)

        if texts_to_embed:
            new_embeddings = self.base_embedder.embed_documents(texts_to_embed)
            
            new_embeddings_iter = iter(new_embeddings)
            for i, emb in enumerate(embeddings):
                if emb is None:
                    text_to_cache = texts_to_embed.pop(0)
                    new_embedding = next(new_embeddings_iter)
                    embeddings[i] = new_embedding
                    self._add_to_cache(text_to_cache, new_embedding)
                    
        return embeddings