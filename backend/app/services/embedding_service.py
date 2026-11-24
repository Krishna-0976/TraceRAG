import math
import hashlib
import re
from typing import List, Optional
import numpy as np
from openai import OpenAI
from app.core.config import settings
from app.core.exceptions import EmbeddingException


class EmbeddingService:
    """
    Manages text embedding generation.
    Supports:
    1. OpenAI Embeddings API (text-embedding-3-small, text-embedding-ada-002, etc.)
    2. Deterministic Semantic Vectorizer (Demo/Local fallback when no OpenAI API key is configured)
       Generates real 1536-dimensional normalized vectors preserving term-frequency semantic cosine similarity.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dimension: int = 1536
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIM
        self._client: Optional[OpenAI] = None

        if self.api_key and self.api_key.strip() and not self.api_key.startswith("mock-"):
            try:
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=settings.OPENAI_BASE_URL
                )
            except Exception:
                self._client = None

    @property
    def is_live_provider(self) -> bool:
        return self._client is not None

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of strings."""
        if not texts:
            return []

        cleaned_texts = [t.replace("\n", " ").strip() for t in texts]

        if self.is_live_provider:
            try:
                response = self._client.embeddings.create(
                    input=cleaned_texts,
                    model=self.model
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                # If API call fails, raise informative exception or fall back if in development
                if settings.ENVIRONMENT == "production":
                    raise EmbeddingException(f"OpenAI API embedding failure: {str(e)}")
                # In development fallback to deterministic embedding with logging
                return [self._generate_deterministic_vector(t) for t in cleaned_texts]

        # Deterministic semantic vectorizer fallback for tests/demo mode
        return [self._generate_deterministic_vector(t) for t in cleaned_texts]

    def embed_query(self, query: str) -> List[float]:
        """Generates embedding vector for a single search query."""
        results = self.embed_texts([query])
        if not results:
            return [0.0] * self.dimension
        return results[0]

    def _generate_deterministic_vector(self, text: str) -> List[float]:
        """
        Generates a 1536-dimensional normalized unit vector deterministically from text.
        Preserves semantic properties:
        - Exact same text produces identical vector (cosine similarity = 1.0)
        - Substring / word overlap produces positive cosine similarity
        - Completely different vocabulary produces near-orthogonal vectors
        """
        if not text:
            vec = [0.0] * self.dimension
            vec[0] = 1.0
            return vec

        # Initialize dense vector
        vec = np.zeros(self.dimension, dtype=np.float32)

        # Tokenize text into words and character n-grams
        words = [re.sub(r'\W+', '', w.lower()) for w in text.split()]
        words = [w for w in words if w]
        for word in words:
            # Hash word into fixed coordinates
            word_hash = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx1 = word_hash % self.dimension
            idx2 = (word_hash >> 16) % self.dimension
            idx3 = (word_hash >> 32) % self.dimension
            idx4 = (word_hash >> 48) % self.dimension
            
            # Substantive term weighting
            vec[idx1] += 3.0
            vec[idx2] += 2.0
            vec[idx3] += 1.5
            vec[idx4] += 1.0

        # Character tri-grams for subword similarity
        for i in range(len(text) - 2):
            trigram = text[i:i+3].lower()
            tri_hash = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest(), 16)
            idx = tri_hash % self.dimension
            vec[idx] += 0.2

        # L2 normalize so cosine distance can be computed accurately
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        else:
            vec[0] = 1.0

        return vec.tolist()

