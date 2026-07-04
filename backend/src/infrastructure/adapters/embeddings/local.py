"""Local embedding adapter for development/testing.

Produces deterministic vectors from text using a simple hash-based approach.
No external API keys required. Each unique text produces the same vector.
"""

import hashlib
import math
import struct


class LocalEmbeddingAdapter:
    """Deterministic embedding adapter for local development.

    Uses a hash-based approach to produce 1536-dimensional vectors
    (matching OpenAI text-embedding-3-small dimension).
    The same text always produces the same vector, enabling
    repeatable similarity search tests without external APIs.
    """

    dimension: int = 1536

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic embeddings for texts."""
        return [self._embed_single(text) for text in texts]

    def _embed_single(self, text: str) -> list[float]:
        """Generate a deterministic embedding vector for a single text.

        Uses SHA-256 of sliding windows of the text to produce
        a pseudo-random but deterministic vector. Positions are
        determined by byte-value hashing so similar texts produce
        similar vectors.
        """
        vec = [0.0] * self.dimension
        word_count = 0

        # Tokenize into words
        words = text.lower().split()
        if not words:
            # Empty text — return a zero vector (not useful but deterministic)
            return vec

        for i, word in enumerate(words):
            word_hash = hashlib.sha256(word.encode()).digest()
            # Use first 8 bytes as a float seed for position
            pos_seed = struct.unpack("<Q", word_hash[:8])[0]
            pos = pos_seed % self.dimension

            # Weight: 1 / (1 + position_in_text) for recency
            weight = 1.0 / (1.0 + i)

            # Accumulate into the vector
            for j in range(4):  # Spread across 4 nearby dimensions
                idx = (pos + j) % self.dimension
                byte_val = word_hash[(j * 4) % 32]
                vec[idx] += (byte_val / 255.0) * weight

            word_count += 1

        # Normalize to unit vector (cosine similarity ready)
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec
