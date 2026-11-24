from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid


class EvaluationDataset(Base, TimestampMixin):
    __tablename__ = "evaluation_datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    questions = relationship("EvaluationQuestion", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("EvaluationRun", back_populates="dataset", cascade="all, delete-orphan")


class EvaluationQuestion(Base, TimestampMixin):
    __tablename__ = "evaluation_questions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=False)
    relevant_document_name = Column(String(255), nullable=False)
    relevant_page = Column(Integer, nullable=True)
    expected_supporting_context = Column(Text, nullable=False)

    # Relationships
    dataset = relationship("EvaluationDataset", back_populates="questions")


class EvaluationRun(Base, TimestampMixin):
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    config = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    
    # Aggregated metrics
    total_questions = Column(Integer, nullable=False, default=0)
    mean_recall_at_k = Column(Float, nullable=False, default=0.0)
    mean_mrr = Column(Float, nullable=False, default=0.0)
    mean_hit_rate_at_k = Column(Float, nullable=False, default=0.0)
    mean_faithfulness = Column(Float, nullable=False, default=0.0)
    mean_answer_correctness = Column(Float, nullable=False, default=0.0)
    mean_citation_correctness = Column(Float, nullable=False, default=0.0)
    
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    dataset = relationship("EvaluationDataset", back_populates="runs")
    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base, TimestampMixin):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    run_id = Column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(36), ForeignKey("evaluation_questions.id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    generated_answer = Column(Text, nullable=False)
    retrieved_chunks = Column(JSON, nullable=False, default=list)
    citations = Column(JSON, nullable=False, default=list)
    
    # Retrieval metrics
    recall_at_k = Column(Float, nullable=False, default=0.0)
    mrr = Column(Float, nullable=False, default=0.0)
    hit_rate_at_k = Column(Float, nullable=False, default=0.0)
    
    # Generation metrics
    faithfulness_score = Column(Float, nullable=False, default=0.0)
    faithfulness_reason = Column(Text, nullable=True)
    answer_correctness_score = Column(Float, nullable=False, default=0.0)
    answer_correctness_reason = Column(Text, nullable=True)
    citation_correctness_score = Column(Float, nullable=False, default=0.0)
    citation_correctness_reason = Column(Text, nullable=True)
    
    execution_time_ms = Column(Float, nullable=False, default=0.0)

    # Relationships
    run = relationship("EvaluationRun", back_populates="results")

