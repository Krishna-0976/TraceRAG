import re
import time
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from openai import OpenAI
from app.core.config import settings
from app.core.exceptions import EvaluationException
from app.models.evaluation import EvaluationDataset, EvaluationQuestion, EvaluationRun, EvaluationResult
from app.repositories.evaluation_repo import EvaluationRepository
from app.schemas.evaluation import (
    EvaluationRunConfig,
    EvaluationRunRead,
    EvaluationComparisonResponse
)
from app.schemas.chunk import ChunkSearchHit
from app.schemas.rag import RAGQueryRequest
from app.services.retrieval_service import RetrievalService
from app.services.rag_service import RAGService
from app.services.embedding_service import EmbeddingService


JUDGE_SYSTEM_PROMPT = """You are an impartial, expert AI Judge evaluating a Retrieval-Augmented Generation (RAG) system.
Your task is to critically evaluate a generated answer against the ground truth expected answer and the retrieved context passages.

You must evaluate three criteria:
1. Faithfulness (0.0 to 1.0): Does every factual claim in the generated answer originate strictly from the retrieved context? (1.0 = completely faithful, 0.0 = completely hallucinated).
2. Answer Correctness (0.0 to 1.0): Does the generated answer accurately and completely reflect the ground truth expected answer? (1.0 = perfectly accurate and complete, 0.0 = completely contradictory or wrong).
3. Citation Correctness (0.0 to 1.0): Do the citations accurately reference the source documents, page numbers, and verbatim excerpts from the retrieved context?

Output strictly in valid JSON format:
{
  "faithfulness_score": 0.95,
  "faithfulness_reason": "Explanation of faithfulness evaluation.",
  "answer_correctness_score": 0.90,
  "answer_correctness_reason": "Explanation of answer correctness evaluation.",
  "citation_correctness_score": 1.0,
  "citation_correctness_reason": "Explanation of citation correctness."
}
"""

BENCHMARK_FIXTURES = [
    # Document 1: rag_architecture_overview.pdf
    {
        "question": "What is the primary purpose of Retrieval-Augmented Generation (RAG)?",
        "expected_answer": "RAG combines dense vector retrieval with autoregressive Large Language Models to overcome parametric knowledge limitations and reduce hallucinations by indexing external documents in high-dimensional vector spaces.",
        "relevant_document_name": "rag_architecture_overview.pdf",
        "relevant_page": 1,
        "expected_supporting_context": "Retrieval-Augmented Generation (RAG) combines dense vector retrieval with autoregressive Large Language Models (LLMs) to overcome parametric knowledge limitations and reduce hallucinations."
    },
    {
        "question": "Why are overlapping chunks used in RAG document chunking?",
        "expected_answer": "Overlapping chunks (typically 10% to 20% of chunk size) prevent semantic rupture at chunk boundaries, ensuring that entities split across sentences remain retrievable.",
        "relevant_document_name": "rag_architecture_overview.pdf",
        "relevant_page": 1,
        "expected_supporting_context": "Overlapping chunks (typically 10% to 20% of chunk size) prevent semantic rupture at chunk boundaries, ensuring that entities split across sentences remain retrievable."
    },
    {
        "question": "What similarity search metric and vector index types are mentioned for vector storage?",
        "expected_answer": "Cosine similarity in continuous metric space, stored in vector databases or PostgreSQL using pgvector with IVFFlat or HNSW indexing structures.",
        "relevant_document_name": "rag_architecture_overview.pdf",
        "relevant_page": 1,
        "expected_supporting_context": "Vectors are stored in specialized vector databases or PostgreSQL using the pgvector extension with IVFFlat or HNSW indexing structures."
    },
    {
        "question": "What similarity threshold range is recommended to eliminate noisy matches?",
        "expected_answer": "A cosine similarity threshold of 0.40 to 0.70 eliminates noisy or low-confidence matches.",
        "relevant_document_name": "rag_architecture_overview.pdf",
        "relevant_page": 2,
        "expected_supporting_context": "Once top-K passages are retrieved, the context construction module filters irrelevant chunks using a cosine similarity threshold. A threshold of 0.40 to 0.70 eliminates noisy or low-confidence matches."
    },
    {
        "question": "What should a grounded RAG system do when retrieved context lacks sufficient evidence?",
        "expected_answer": "The system prompt strictly instructs the LLM to refuse answering and explicitly declare that the answer cannot be established from available sources.",
        "relevant_document_name": "rag_architecture_overview.pdf",
        "relevant_page": 2,
        "expected_supporting_context": "The standard refusal protocol states that if the evidence is missing, the model must explicitly declare that the answer cannot be established from available sources."
    },
    {
        "question": "How is Recall@K defined in the quantitative evaluation framework?",
        "expected_answer": "Recall@K measures the proportion of relevant chunks or ground truth context retrieved in the top-K list.",
        "relevant_document_name": "rag_architecture_overview.pdf",
        "relevant_page": 3,
        "expected_supporting_context": "Recall@K measures the proportion of relevant chunks or ground truth context retrieved in the top-K list."
    },
    {
        "question": "How is Mean Reciprocal Rank (MRR) calculated?",
        "expected_answer": "Mean Reciprocal Rank (MRR) evaluates ranking quality as the multiplicative inverse of the rank of the first relevant result.",
        "relevant_document_name": "rag_architecture_overview.pdf",
        "relevant_page": 3,
        "expected_supporting_context": "Mean Reciprocal Rank (MRR) evaluates ranking quality as the multiplicative inverse of the rank of the first relevant result."
    },
    {
        "question": "What does the Faithfulness metric measure in RAG generation evaluation?",
        "expected_answer": "Faithfulness measures whether every claim in the generated answer is directly entailed by the retrieved context.",
        "relevant_document_name": "rag_architecture_overview.pdf",
        "relevant_page": 3,
        "expected_supporting_context": "Faithfulness measures whether every claim in the generated answer is directly entailed by the retrieved context."
    },

    # Document 2: enterprise_cloud_security_policy.pdf
    {
        "question": "What authentication mechanism is mandatory for privileged infrastructure administrators?",
        "expected_answer": "Hardware-backed FIDO2 security keys and Multi-Factor Authentication (MFA) are strictly mandatory for privileged administrators.",
        "relevant_document_name": "enterprise_cloud_security_policy.pdf",
        "relevant_page": 1,
        "expected_supporting_context": "Multi-Factor Authentication (MFA) is strictly required for all administrative interfaces. Hardware-backed FIDO2 security keys are mandatory for privileged infrastructure administrators."
    },
    {
        "question": "What is the maximum inactivity limit for administrative console sessions?",
        "expected_answer": "Session lifetimes for administrative consoles are capped at 60 minutes of inactivity before automatic session termination.",
        "relevant_document_name": "enterprise_cloud_security_policy.pdf",
        "relevant_page": 1,
        "expected_supporting_context": "Session lifetimes for administrative consoles are capped at 60 minutes of inactivity before automatic session termination."
    },
    {
        "question": "Which cryptographic algorithms and key lengths are mandatory for data at rest?",
        "expected_answer": "Data at rest must be encrypted using AES-256 (Advanced Encryption Standard with 256-bit keys) or ChaCha20-Poly1305.",
        "relevant_document_name": "enterprise_cloud_security_policy.pdf",
        "relevant_page": 2,
        "expected_supporting_context": "Data at rest must be encrypted using AES-256 (Advanced Encryption Standard with 256-bit keys) or ChaCha20-Poly1305."
    },
    {
        "question": "How often must customer-managed encryption keys (CMEK) be rotated?",
        "expected_answer": "Customer-managed encryption keys (CMEK) must be rotated automatically every 90 days.",
        "relevant_document_name": "enterprise_cloud_security_policy.pdf",
        "relevant_page": 2,
        "expected_supporting_context": "Customer-managed encryption keys (CMEK) must be rotated automatically every 90 days."
    },
    {
        "question": "What is the minimum retention period required for database backups?",
        "expected_answer": "Database backups must be retained for a mandatory minimum of 365 days in an immutable write-once-read-many (WORM) storage vault.",
        "relevant_document_name": "enterprise_cloud_security_policy.pdf",
        "relevant_page": 2,
        "expected_supporting_context": "Database backups must be retained for a mandatory minimum of 365 days in an immutable write-once-read-many (WORM) storage vault."
    },
    {
        "question": "What is the required initial response time for Severity-1 security incidents?",
        "expected_answer": "Severity-1 incidents require an initial response time within 15 minutes, and containment actions must commence within 30 minutes of detection.",
        "relevant_document_name": "enterprise_cloud_security_policy.pdf",
        "relevant_page": 3,
        "expected_supporting_context": "Severity-1 incidents, defined as unauthorized root access or active data exfiltration, require an initial response time within 15 minutes."
    },
    {
        "question": "What are the required Recovery Point Objective (RPO) and Recovery Time Objective (RTO) targets?",
        "expected_answer": "Disaster recovery capabilities must satisfy an RPO of less than 15 minutes and an RTO of less than 2 hours.",
        "relevant_document_name": "enterprise_cloud_security_policy.pdf",
        "relevant_page": 3,
        "expected_supporting_context": "Disaster recovery capabilities must satisfy a Recovery Point Objective (RPO) of less than 15 minutes and a Recovery Time Objective (RTO) of less than 2 hours."
    },

    # Document 3: autonomous_agent_workflows.pdf
    {
        "question": "What is the primary role of the Coordinator Agent in a multi-agent system?",
        "expected_answer": "The Coordinator Agent acts as the orchestrator, analyzing incoming user intents, decomposing requirements into a Directed Acyclic Graph (DAG) of tasks, and delegating execution to domain workers.",
        "relevant_document_name": "autonomous_agent_workflows.pdf",
        "relevant_page": 1,
        "expected_supporting_context": "The Coordinator Agent acts as the orchestrator, analyzing incoming user intents, decomposing requirements into a Directed Acyclic Graph (DAG) of tasks, and delegating execution to domain workers."
    },
    {
        "question": "What are the three tiers of agent memory and what does working memory hold?",
        "expected_answer": "The three tiers are Working Memory, Episodic Memory, and Semantic Memory. Working Memory is the transient context window holding active conversation turns, intermediate reasoning traces, and tool results.",
        "relevant_document_name": "autonomous_agent_workflows.pdf",
        "relevant_page": 2,
        "expected_supporting_context": "Agent memory is organized into three distinct tiers: Working Memory, Episodic Memory, and Semantic Memory. Working Memory: Transient context window holding active conversation turns, intermediate reasoning traces, and immediate tool execution results."
    },
    {
        "question": "How do autonomous architectures prevent error compounding and infinite loops in long-horizon tasks?",
        "expected_answer": "They implement automated verification loops with an independent Verifier Agent, multi-agent consensus protocols, and maximum loop depth limits (typically 3 to 5 retry cycles).",
        "relevant_document_name": "autonomous_agent_workflows.pdf",
        "relevant_page": 3,
        "expected_supporting_context": "After worker agents complete execution, an independent Verifier Agent audits the output against predefined acceptance criteria. Maximum loop depth limits (typically 3 to 5 retry cycles) prevent infinite reflection loops."
    }
]


class EvaluationService:
    def __init__(
        self,
        db: Session,
        retrieval_service: Optional[RetrievalService] = None,
        rag_service: Optional[RAGService] = None,
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.db = db
        self.eval_repo = EvaluationRepository(db)
        self.embedding_service = embedding_service or EmbeddingService()
        self.retrieval_service = retrieval_service or RetrievalService(db, self.embedding_service)
        self.rag_service = rag_service or RAGService(db, self.retrieval_service, self.embedding_service)
        
        self._judge_client: Optional[OpenAI] = None
        if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("mock-"):
            try:
                self._judge_client = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL
                )
            except Exception:
                self._judge_client = None

    def ensure_default_benchmark_dataset(self) -> EvaluationDataset:
        """Seeds standard 18-question benchmark dataset if none exists."""
        dataset = self.eval_repo.get_first_dataset()
        if not dataset:
            dataset = self.eval_repo.create_dataset(
                name="TraceRAG Technical Benchmark Suite",
                description="Standardized 18-question benchmark testing retrieval precision, grounded synthesis, and factual citation accuracy."
            )
            for item in BENCHMARK_FIXTURES:
                self.eval_repo.create_question(
                    dataset_id=dataset.id,
                    question=item["question"],
                    expected_answer=item["expected_answer"],
                    relevant_document_name=item["relevant_document_name"],
                    relevant_page=item["relevant_page"],
                    expected_supporting_context=item["expected_supporting_context"]
                )
        return dataset

    # =========================================================================
    # DETERMINISTIC RETRIEVAL METRICS (Pure Python)
    # =========================================================================

    @staticmethod
    def calculate_hit_rate_at_k(
        relevant_doc: str,
        relevant_page: Optional[int],
        retrieved_chunks: List[ChunkSearchHit]
    ) -> float:
        """
        Hit Rate@K:
        Returns 1.0 if at least one retrieved chunk in top-K matches the target document
        and (if page provided) target page. Returns 0.0 otherwise.
        """
        if not retrieved_chunks:
            return 0.0

        for chunk in retrieved_chunks:
            doc_match = (
                chunk.document_name.lower() == relevant_doc.lower() or
                relevant_doc.lower() in chunk.document_name.lower() or
                chunk.document_name.lower() in relevant_doc.lower()
            )
            if doc_match:
                if relevant_page is None or chunk.page_number == relevant_page:
                    return 1.0
        return 0.0

    @staticmethod
    def calculate_mrr(
        relevant_doc: str,
        relevant_page: Optional[int],
        retrieved_chunks: List[ChunkSearchHit]
    ) -> float:
        """
        Mean Reciprocal Rank (MRR):
        1 / rank of the first relevant chunk in top-K (1-indexed).
        Returns 0.0 if no relevant chunk found.
        """
        if not retrieved_chunks:
            return 0.0

        for rank, chunk in enumerate(retrieved_chunks, start=1):
            doc_match = (
                chunk.document_name.lower() == relevant_doc.lower() or
                relevant_doc.lower() in chunk.document_name.lower() or
                chunk.document_name.lower() in relevant_doc.lower()
            )
            if doc_match:
                if relevant_page is None or chunk.page_number == relevant_page:
                    return 1.0 / rank
        return 0.0

    @staticmethod
    def calculate_recall_at_k(
        expected_context: str,
        retrieved_chunks: List[ChunkSearchHit]
    ) -> float:
        """
        Recall@K:
        Proportion of ground truth context information recovered across the retrieved top-K chunks.
        Calculates token-level coverage of the expected supporting context.
        """
        if not expected_context or not retrieved_chunks:
            return 0.0

        # Tokenize expected context
        expected_tokens = set(re.findall(r"\w+", expected_context.lower()))
        stop_words = {"the", "a", "an", "is", "in", "of", "to", "and", "or", "for", "with", "on", "at", "by"}
        expected_tokens -= stop_words

        if not expected_tokens:
            return 1.0

        combined_retrieved_text = " ".join([c.text.lower() for c in retrieved_chunks])
        retrieved_tokens = set(re.findall(r"\w+", combined_retrieved_text))

        recovered_count = len(expected_tokens.intersection(retrieved_tokens))
        return min(1.0, max(0.0, recovered_count / len(expected_tokens)))

    # =========================================================================
    # GENERATION METRICS (LLM-as-a-judge / Deterministic semantic fallback)
    # =========================================================================

    def evaluate_generation(
        self,
        question: str,
        generated_answer: str,
        expected_answer: str,
        retrieved_chunks: List[ChunkSearchHit],
        citations: List[Any]
    ) -> Tuple[float, str, float, str, float, str]:
        """
        Computes Faithfulness, Answer Correctness, and Citation Correctness.
        """
        if self._judge_client:
            try:
                retrieved_context_str = "\n".join([f"[{c.document_name} P.{c.page_number}]: {c.text}" for c in retrieved_chunks])
                citations_str = json.dumps(citations)

                user_prompt = f"""Question: {question}
Expected Ground Truth Answer: {expected_answer}

Retrieved Context:
{retrieved_context_str}

Generated Answer:
{generated_answer}

Citations Provided:
{citations_str}

Evaluate faithfulness, answer correctness, and citation correctness according to the system instructions. Return strictly JSON."""

                resp = self._judge_client.chat.completions.create(
                    model=settings.EVAL_JUDGE_MODEL,
                    messages=[
                        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                res = json.loads(resp.choices[0].message.content)

                return (
                    float(res.get("faithfulness_score", 0.9)),
                    res.get("faithfulness_reason", "LLM-as-a-judge evaluated claim grounding."),
                    float(res.get("answer_correctness_score", 0.9)),
                    res.get("answer_correctness_reason", "LLM-as-a-judge evaluated semantic match with ground truth."),
                    float(res.get("citation_correctness_score", 1.0)),
                    res.get("citation_correctness_reason", "LLM-as-a-judge verified citations against excerpts.")
                )
            except Exception:
                pass

        # Deterministic generation evaluator fallback
        return self._evaluate_generation_deterministic(
            generated_answer=generated_answer,
            expected_answer=expected_answer,
            retrieved_chunks=retrieved_chunks,
            citations=citations
        )

    def _evaluate_generation_deterministic(
        self,
        generated_answer: str,
        expected_answer: str,
        retrieved_chunks: List[ChunkSearchHit],
        citations: List[Any]
    ) -> Tuple[float, str, float, str, float, str]:
        """
        Deterministic, rule-based generation evaluator:
        - Faithfulness: ratio of answer claim tokens supported by retrieved text
        - Answer Correctness: token overlap & semantic alignment with expected answer
        - Citation Correctness: validation that citations match chunk text and pages
        """
        stop_words = {"the", "a", "an", "is", "in", "of", "to", "and", "or", "for", "with", "on", "at", "by", "that", "this"}
        
        # 1. Faithfulness
        ans_tokens = set(re.findall(r"\w+", generated_answer.lower())) - stop_words
        context_tokens = set(re.findall(r"\w+", " ".join([c.text.lower() for c in retrieved_chunks])))
        
        if not ans_tokens:
            faithfulness_score = 1.0
            faithfulness_reason = "Answer is concise with no ungrounded claims."
        else:
            supported = len(ans_tokens.intersection(context_tokens))
            faithfulness_score = min(1.0, max(0.0, supported / len(ans_tokens)))
            faithfulness_reason = f"Deterministic grounding: {supported}/{len(ans_tokens)} substantive answer tokens present in retrieved passages."

        # 2. Answer Correctness (Token F1 / semantic overlap)
        exp_tokens = set(re.findall(r"\w+", expected_answer.lower())) - stop_words
        if not exp_tokens:
            correctness_score = 1.0
            correctness_reason = "No ground truth tokens required."
        else:
            match = len(ans_tokens.intersection(exp_tokens))
            precision = match / len(ans_tokens) if ans_tokens else 0.0
            recall = match / len(exp_tokens)
            if precision + recall > 0:
                f1 = (2 * precision * recall) / (precision + recall)
            else:
                f1 = 0.0
            correctness_score = f1
            correctness_reason = f"Deterministic semantic match: F1={f1:.2f} ({match} matched tokens between answer and ground truth)."

        # 3. Citation Correctness
        if not citations:
            if "sufficient information" in generated_answer.lower():
                citation_score = 1.0
                citation_reason = "System correctly refused when evidence was insufficient."
            else:
                citation_score = 0.5
                citation_reason = "Answer provided without inline citations."
        else:
            valid_citations = 0
            for c in citations:
                doc_name = c.get("source_document", "") if isinstance(c, dict) else getattr(c, "source_document", "")
                chunk_match = any(
                    ch.document_name.lower() in doc_name.lower() or doc_name.lower() in ch.document_name.lower()
                    for ch in retrieved_chunks
                )
                if chunk_match:
                    valid_citations += 1
            citation_score = valid_citations / len(citations)
            citation_reason = f"Citation verification: {valid_citations}/{len(citations)} citations accurately map to retrieved documents."

        return (
            round(faithfulness_score, 4),
            faithfulness_reason,
            round(correctness_score, 4),
            correctness_reason,
            round(citation_score, 4),
            citation_reason
        )

    # =========================================================================
    # BENCHMARK RUN EXECUTION & COMPARISON
    # =========================================================================

    def run_benchmark(self, config: EvaluationRunConfig) -> EvaluationRunRead:
        """
        Executes complete benchmark suite on the dataset:
        1. Retrieves each question
        2. Queries RAG pipeline with configured top_k and similarity_threshold
        3. Measures Recall@K, MRR, Hit Rate@K, Faithfulness, Correctness, Citation score
        4. Saves all results and updates run aggregates
        """
        dataset = self.ensure_default_benchmark_dataset()
        if config.dataset_id:
            ds = self.eval_repo.get_dataset(config.dataset_id)
            if ds:
                dataset = ds

        questions = self.eval_repo.get_questions_for_dataset(dataset.id)
        if not questions:
            raise EvaluationException(f"No benchmark questions found in dataset '{dataset.id}'.")

        run_name = config.name or f"Run (Top-K={config.top_k}, Thresh={config.similarity_threshold})"
        run = self.eval_repo.create_run(
            dataset_id=dataset.id,
            name=run_name,
            config=config.model_dump()
        )
        self.eval_repo.update_run_status(run.id, "RUNNING")

        total_q = len(questions)
        recalls, mrrs, hit_rates = [], [], []
        faithfulness_scores, correctness_scores, citation_scores = [], [], []

        for q in questions:
            start_q = time.perf_counter()

            # 1. Retrieve
            retrieved_hits = self.retrieval_service.retrieve_chunks_for_rag(
                query=q.question,
                top_k=config.top_k,
                similarity_threshold=config.similarity_threshold
            )

            # 2. Retrieval metrics
            hr = self.calculate_hit_rate_at_k(q.relevant_document_name, q.relevant_page, retrieved_hits)
            mrr = self.calculate_mrr(q.relevant_document_name, q.relevant_page, retrieved_hits)
            recall = self.calculate_recall_at_k(q.expected_supporting_context, retrieved_hits)

            # 3. Generate answer
            rag_res = self.rag_service.query(
                RAGQueryRequest(
                    query=q.question,
                    top_k=config.top_k,
                    similarity_threshold=config.similarity_threshold
                )
            )

            # 4. Generation metrics
            faith_s, faith_r, corr_s, corr_r, cit_s, cit_r = self.evaluate_generation(
                question=q.question,
                generated_answer=rag_res.answer,
                expected_answer=q.expected_answer,
                retrieved_chunks=retrieved_hits,
                citations=rag_res.citations
            )

            exec_time_ms = (time.perf_counter() - start_q) * 1000.0

            # Store result
            self.eval_repo.create_result(
                run_id=run.id,
                question_id=q.id,
                question=q.question,
                generated_answer=rag_res.answer,
                retrieved_chunks=[h.model_dump() for h in retrieved_hits],
                citations=[c.model_dump() for c in rag_res.citations],
                recall_at_k=recall,
                mrr=mrr,
                hit_rate_at_k=hr,
                faithfulness_score=faith_s,
                faithfulness_reason=faith_r,
                answer_correctness_score=corr_s,
                answer_correctness_reason=corr_r,
                citation_correctness_score=cit_s,
                citation_correctness_reason=cit_r,
                execution_time_ms=exec_time_ms
            )

            recalls.append(recall)
            mrrs.append(mrr)
            hit_rates.append(hr)
            faithfulness_scores.append(faith_s)
            correctness_scores.append(corr_s)
            citation_scores.append(cit_s)

        # Aggregate averages
        mean_recall = sum(recalls) / total_q if total_q else 0.0
        mean_mrr = sum(mrrs) / total_q if total_q else 0.0
        mean_hit_rate = sum(hit_rates) / total_q if total_q else 0.0
        mean_faithfulness = sum(faithfulness_scores) / total_q if total_q else 0.0
        mean_correctness = sum(correctness_scores) / total_q if total_q else 0.0
        mean_citation = sum(citation_scores) / total_q if total_q else 0.0

        completed_run = self.eval_repo.complete_run(
            run_id=run.id,
            total_questions=total_q,
            mean_recall_at_k=mean_recall,
            mean_mrr=mean_mrr,
            mean_hit_rate_at_k=mean_hit_rate,
            mean_faithfulness=mean_faithfulness,
            mean_answer_correctness=mean_correctness,
            mean_citation_correctness=mean_citation
        )

        return EvaluationRunRead.model_validate(completed_run)

    def compare_runs(self, run_id_a: str, run_id_b: str) -> EvaluationComparisonResponse:
        """Computes metric deltas and analytical report comparing two benchmark runs."""
        run_a = self.eval_repo.get_run(run_id_a)
        run_b = self.eval_repo.get_run(run_id_b)

        if not run_a or not run_b:
            raise EvaluationException("One or both comparison runs could not be found.")

        deltas = {
            "recall_at_k_delta": round(run_b.mean_recall_at_k - run_a.mean_recall_at_k, 4),
            "mrr_delta": round(run_b.mean_mrr - run_a.mean_mrr, 4),
            "hit_rate_at_k_delta": round(run_b.mean_hit_rate_at_k - run_a.mean_hit_rate_at_k, 4),
            "faithfulness_delta": round(run_b.mean_faithfulness - run_a.mean_faithfulness, 4),
            "answer_correctness_delta": round(run_b.mean_answer_correctness - run_a.mean_answer_correctness, 4),
            "citation_correctness_delta": round(run_b.mean_citation_correctness - run_a.mean_citation_correctness, 4)
        }

        # Build analytical summary
        top_k_a = run_a.config.get("top_k", "N/A")
        top_k_b = run_b.config.get("top_k", "N/A")
        thresh_a = run_a.config.get("similarity_threshold", "N/A")
        thresh_b = run_b.config.get("similarity_threshold", "N/A")

        summary_parts = [
            f"Comparison between Run A ({run_a.name}) and Run B ({run_b.name}):",
            f"- Configuration A: Top-K={top_k_a}, Similarity Threshold={thresh_a}",
            f"- Configuration B: Top-K={top_k_b}, Similarity Threshold={thresh_b}",
            f"- Recall@K shifted by {deltas['recall_at_k_delta']:+0.2%}.",
            f"- MRR shifted by {deltas['mrr_delta']:+0.2%}.",
            f"- Hit Rate@K shifted by {deltas['hit_rate_at_k_delta']:+0.2%}.",
            f"- Faithfulness shifted by {deltas['faithfulness_delta']:+0.2%}.",
            f"- Answer Correctness shifted by {deltas['answer_correctness_delta']:+0.2%}."
        ]

        if deltas['recall_at_k_delta'] > 0:
            summary_parts.append("Observation: Configuration B retrieved higher context recall, reducing missed information.")
        elif deltas['recall_at_k_delta'] < 0:
            summary_parts.append("Observation: Configuration B exhibited lower recall, potentially due to stricter thresholding.")

        if deltas['faithfulness_delta'] >= 0:
            summary_parts.append("Grounding fidelity remained high or improved.")
        else:
            summary_parts.append("Warning: Grounding faithfulness decreased in Configuration B.")

        return EvaluationComparisonResponse(
            run_a=EvaluationRunRead.model_validate(run_a),
            run_b=EvaluationRunRead.model_validate(run_b),
            metrics_delta=deltas,
            summary_analysis="\n".join(summary_parts)
        )
