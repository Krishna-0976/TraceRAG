from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.rag import Citation
from app.schemas.chunk import ChunkSearchHit


class EvaluationQuestionBase(BaseModel):
    question: str
    expected_answer: str
    relevant_document_name: str
    relevant_page: Optional[int] = None
    expected_supporting_context: str


class EvaluationQuestionCreate(EvaluationQuestionBase):
    pass


class EvaluationQuestionRead(EvaluationQuestionBase):
    id: str
    dataset_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvaluationDatasetRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    questions: List[EvaluationQuestionRead] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunConfig(BaseModel):
    name: Optional[str] = "Benchmark Run"
    dataset_id: Optional[str] = None
    top_k: int = Field(default=4, ge=1, le=20)
    similarity_threshold: float = Field(default=0.40, ge=0.0, le=1.0)
    chunk_size: Optional[int] = Field(default=500, description="Chunk size if re-chunking")
    chunk_overlap: Optional[int] = Field(default=100, description="Chunk overlap if re-chunking")
    embedding_model: Optional[str] = "text-embedding-3-small"
    llm_model: Optional[str] = "gpt-4o-mini"


class EvaluationResultRead(BaseModel):
    id: str
    run_id: str
    question_id: Optional[str]
    question: str
    generated_answer: str
    retrieved_chunks: List[Any] = Field(default_factory=list)
    citations: List[Any] = Field(default_factory=list)
    recall_at_k: float
    mrr: float
    hit_rate_at_k: float
    faithfulness_score: float
    faithfulness_reason: Optional[str] = None
    answer_correctness_score: float
    answer_correctness_reason: Optional[str] = None
    citation_correctness_score: float
    citation_correctness_reason: Optional[str] = None
    execution_time_ms: float
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunRead(BaseModel):
    id: str
    dataset_id: str
    name: str
    config: Dict[str, Any]
    status: str
    error_message: Optional[str] = None
    total_questions: int
    mean_recall_at_k: float
    mean_mrr: float
    mean_hit_rate_at_k: float
    mean_faithfulness: float
    mean_answer_correctness: float
    mean_citation_correctness: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: List[EvaluationResultRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class EvaluationComparisonRequest(BaseModel):
    run_id_a: str
    run_id_b: str


class EvaluationComparisonResponse(BaseModel):
    run_a: EvaluationRunRead
    run_b: EvaluationRunRead
    metrics_delta: Dict[str, float]
    summary_analysis: str
