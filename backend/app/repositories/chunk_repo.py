import math
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.schemas.chunk import DocumentChunkCreate, ChunkSearchHit


class ChunkRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_create(self, chunks: List[DocumentChunkCreate]) -> List[DocumentChunk]:
        db_chunks = [
            DocumentChunk(
                document_id=c.document_id,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                text=c.text,
                token_count=c.token_count,
                embedding=c.embedding,
                metadata_json=c.metadata_json
            )
            for c in chunks
        ]
        self.db.add_all(db_chunks)
        self.db.commit()
        return db_chunks

    def get_by_document(self, document_id: str) -> List[DocumentChunk]:
        return (
            self.db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

    def count_all(self) -> int:
        return self.db.query(DocumentChunk).count()

    def delete_by_document(self, document_id: str) -> int:
        count = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        self.db.commit()
        return count

    def search_vector(
        self,
        query_vector: List[float],
        top_k: int = 4,
        similarity_threshold: float = 0.40,
        document_ids: Optional[List[str]] = None
    ) -> List[ChunkSearchHit]:
        """
        Executes vector cosine similarity search:
        - If PostgreSQL dialect: utilizes pgvector <=> cosine distance operator
        - If SQLite or other: performs in-memory cosine similarity calculation
        """
        dialect_name = self.db.bind.dialect.name if self.db.bind else "sqlite"
        
        if dialect_name == "postgresql":
            # PostgreSQL + pgvector query
            # Cosine similarity = 1 - cosine distance
            query = self.db.query(DocumentChunk, Document.filename).join(Document, DocumentChunk.document_id == Document.id)
            if document_ids:
                query = query.filter(DocumentChunk.document_id.in_(document_ids))
            
            # Using pgvector distance operator: 1 - (embedding <=> :vec)
            # Or order by DocumentChunk.embedding.cosine_distance(query_vector)
            results = (
                query.order_by(DocumentChunk.embedding.cosine_distance(query_vector))
                .limit(top_k * 2)
                .all()
            )
            
            hits: List[ChunkSearchHit] = []
            for chunk, filename in results:
                if chunk.embedding is None:
                    continue
                # Calculate exact cosine similarity
                sim = self._calculate_cosine_similarity(query_vector, chunk.embedding)
                if sim >= similarity_threshold:
                    hits.append(
                        ChunkSearchHit(
                            id=chunk.id,
                            document_id=chunk.document_id,
                            document_name=filename,
                            chunk_index=chunk.chunk_index,
                            page_number=chunk.page_number,
                            text=chunk.text,
                            similarity_score=round(sim, 4),
                            token_count=chunk.token_count,
                            metadata_json=chunk.metadata_json or {}
                        )
                    )
            return sorted(hits, key=lambda x: x.similarity_score, reverse=True)[:top_k]

        else:
            # SQLite / Fallback vector search
            query = self.db.query(DocumentChunk, Document.filename).join(Document, DocumentChunk.document_id == Document.id)
            if document_ids:
                query = query.filter(DocumentChunk.document_id.in_(document_ids))
            all_chunks = query.all()

            scored_chunks: List[Tuple[DocumentChunk, str, float]] = []
            for chunk, filename in all_chunks:
                if not chunk.embedding:
                    continue
                score = self._calculate_cosine_similarity(query_vector, chunk.embedding)
                if score >= similarity_threshold:
                    scored_chunks.append((chunk, filename, score))

            scored_chunks.sort(key=lambda x: x[2], reverse=True)
            top_results = scored_chunks[:top_k]

            return [
                ChunkSearchHit(
                    id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=filename,
                    chunk_index=chunk.chunk_index,
                    page_number=chunk.page_number,
                    text=chunk.text,
                    similarity_score=round(score, 4),
                    token_count=chunk.token_count,
                    metadata_json=chunk.metadata_json or {}
                )
                for chunk, filename, score in top_results
            ]

    @staticmethod
    def _calculate_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return max(0.0, min(1.0, dot_product / (norm_a * norm_b)))

