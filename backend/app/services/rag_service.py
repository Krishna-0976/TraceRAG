import json
import time
import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from openai import OpenAI
from app.core.config import settings
from app.core.exceptions import GenerationException
from app.models.conversation import Conversation, Message
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.rag import RAGQueryRequest, RAGResponse, Citation
from app.schemas.chunk import ChunkSearchHit
from app.services.retrieval_service import RetrievalService
from app.services.embedding_service import EmbeddingService


RAG_SYSTEM_PROMPT = """You are TraceRAG, a high-precision, evidence-grounded AI knowledge engine.
Your sole purpose is to answer questions strictly and faithfully based on the retrieved context passages provided below.

Strict Constraints:
1. Grounding: Answer ONLY using facts directly stated in the context passages. Do NOT assume, extrapolate, or use outside knowledge.
2. Refusal: If the provided passages do not contain sufficient evidence to answer the question with certainty, you MUST state clearly:
   "The available source documents do not contain sufficient information to answer this question."
   Set "is_refusal": true and "citations": [].
3. Citations: Every fact or claim in your answer must cite its exact source document and page number.
   Provide exact, verbatim short excerpts from the passages to substantiate each citation.
4. Output Format: You MUST reply in valid JSON adhering strictly to this schema:
{
  "answer": "Detailed, evidence-grounded answer text.",
  "is_refusal": false,
  "citations": [
    {
      "source_document": "filename.pdf",
      "page_number": 1,
      "excerpt": "verbatim text excerpt from the context passage supporting this fact",
      "chunk_id": "id-of-chunk"
    }
  ]
}
"""


class RAGService:
    def __init__(
        self,
        db: Session,
        retrieval_service: Optional[RetrievalService] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.db = db
        self.conv_repo = ConversationRepository(db)
        self.embedding_service = embedding_service or EmbeddingService()
        self.retrieval_service = retrieval_service or RetrievalService(db, self.embedding_service)
        
        self._openai_client: Optional[OpenAI] = None
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock-"):
            try:
                self._openai_client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL
                )
            except Exception:
                self._openai_client = None

    def query(self, request: RAGQueryRequest) -> RAGResponse:
        start_time = time.perf_counter()

        # 1. Conversation management
        conv_id = request.conversation_id
        if not conv_id:
            conv = self.conv_repo.create_conversation(title=f"Query: {request.query[:30]}...")
            conv_id = conv.id
        else:
            conv = self.conv_repo.get_conversation(conv_id)
            if not conv:
                conv = self.conv_repo.create_conversation(title=f"Query: {request.query[:30]}...")
                conv_id = conv.id

        # Record user message
        self.conv_repo.create_message(
            conversation_id=conv_id,
            role="user",
            content=request.query
        )

        # 2. Vector Retrieval
        retrieved_hits = self.retrieval_service.retrieve_chunks_for_rag(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            document_ids=request.document_ids
        )

        # 3. Context Check
        if not retrieved_hits:
            refusal_text = "The available source documents do not contain sufficient information to answer this question."
            msg = self.conv_repo.create_message(
                conversation_id=conv_id,
                role="assistant",
                content=refusal_text,
                citations=[],
                retrieved_chunks=[]
            )
            exec_time = (time.perf_counter() - start_time) * 1000.0
            return RAGResponse(
                answer=refusal_text,
                citations=[],
                retrieved_chunks=[],
                conversation_id=conv_id,
                message_id=msg.id,
                grounded=True,
                is_refusal=True,
                execution_time_ms=round(exec_time, 2)
            )

        # 4. Context Construction
        context_blocks = []
        for i, hit in enumerate(retrieved_hits):
            context_blocks.append(
                f"[Passage {i+1}]\n"
                f"Document: {hit.document_name}\n"
                f"Page: {hit.page_number}\n"
                f"Chunk ID: {hit.id}\n"
                f"Similarity Score: {hit.similarity_score}\n"
                f"Content:\n{hit.text}\n"
            )
        context_str = "\n".join(context_blocks)

        # 5. LLM Generation
        answer_text, citations, is_refusal = self._generate_answer(
            query=request.query,
            context_str=context_str,
            retrieved_hits=retrieved_hits
        )

        # 6. Save Assistant Message
        msg = self.conv_repo.create_message(
            conversation_id=conv_id,
            role="assistant",
            content=answer_text,
            citations=[c.model_dump() for c in citations],
            retrieved_chunks=[h.model_dump() for h in retrieved_hits]
        )

        exec_time = (time.perf_counter() - start_time) * 1000.0

        return RAGResponse(
            answer=answer_text,
            citations=citations,
            retrieved_chunks=retrieved_hits,
            conversation_id=conv_id,
            message_id=msg.id,
            grounded=not is_refusal and len(citations) > 0,
            is_refusal=is_refusal,
            execution_time_ms=round(exec_time, 2)
        )

    def _generate_answer(
        self,
        query: str,
        context_str: str,
        retrieved_hits: List[ChunkSearchHit]
    ) -> tuple[str, List[Citation], bool]:
        """Invokes LLM API or deterministic fallback engine."""
        if self._openai_client:
            try:
                user_prompt = f"Context Passages:\n{context_str}\n\nQuestion: {query}\n\nProvide your grounded answer with citations in the required JSON format."
                
                response = self._openai_client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": RAG_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                raw_json = response.choices[0].message.content
                parsed = json.loads(raw_json)

                answer = parsed.get("answer", "")
                is_refusal = bool(parsed.get("is_refusal", False))
                raw_citations = parsed.get("citations", [])

                # Validate and link citations with retrieved hits
                citations: List[Citation] = []
                if not is_refusal:
                    hit_map = {h.id: h for h in retrieved_hits}
                    for c in raw_citations:
                        chunk_id = c.get("chunk_id", "")
                        matching_hit = hit_map.get(chunk_id)
                        if not matching_hit:
                            # Try finding by document name
                            for h in retrieved_hits:
                                if h.document_name == c.get("source_document"):
                                    matching_hit = h
                                    chunk_id = h.id
                                    break
                        
                        citations.append(
                            Citation(
                                source_document=c.get("source_document") or (matching_hit.document_name if matching_hit else "Unknown"),
                                document_id=matching_hit.document_id if matching_hit else "",
                                page_number=int(c.get("page_number", matching_hit.page_number if matching_hit else 1)),
                                excerpt=c.get("excerpt", ""),
                                chunk_id=chunk_id,
                                similarity_score=matching_hit.similarity_score if matching_hit else 0.5
                            )
                        )

                return answer, citations, is_refusal

            except Exception as e:
                if settings.ENVIRONMENT == "production":
                    raise GenerationException(f"OpenAI completion error: {str(e)}")
                # In development/fallback, proceed to deterministic grounded synthesis

        # Deterministic Grounded Generation Fallback (Demo/Offline Mode)
        return self._generate_deterministic_grounded_answer(query, retrieved_hits)

    def _generate_deterministic_grounded_answer(
        self,
        query: str,
        retrieved_hits: List[ChunkSearchHit]
    ) -> tuple[str, List[Citation], bool]:
        """
        Deterministic, faithful answer generator for offline/demo operation.
        Verifies exact presence of answer material in chunks.
        """
        query_words = set(re.findall(r"\w+", query.lower()))
        # Filter stop words
        stop_words = {"what", "is", "the", "how", "why", "who", "when", "where", "does", "do", "a", "an", "in", "of", "to", "for", "and", "or"}
        key_words = query_words - stop_words

        candidate_sentences = []
        citations: List[Citation] = []

        for hit in retrieved_hits:
            sentences = re.split(r"(?<=[.!?])\s+", hit.text)
            for s in sentences:
                s_words = set(re.findall(r"\w+", s.lower()))
                overlap = len(key_words.intersection(s_words))
                if overlap > 0:
                    candidate_sentences.append((overlap, s.strip(), hit))

        if not candidate_sentences:
            return (
                "The available source documents do not contain sufficient information to answer this question.",
                [],
                True
            )

        candidate_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = candidate_sentences[:3]

        answer_parts = []
        for _, s, hit in top_sentences:
            answer_parts.append(s)
            citations.append(
                Citation(
                    source_document=hit.document_name,
                    document_id=hit.document_id,
                    page_number=hit.page_number,
                    excerpt=s[:150],
                    chunk_id=hit.id,
                    similarity_score=hit.similarity_score
                )
            )

        answer_text = " ".join(answer_parts)
        return answer_text, citations, False

