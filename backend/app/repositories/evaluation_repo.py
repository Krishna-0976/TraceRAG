from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.evaluation import (
    EvaluationDataset,
    EvaluationQuestion,
    EvaluationRun,
    EvaluationResult
)


class EvaluationRepository:
    def __init__(self, db: Session):
        self.db = db

    # Datasets
    def get_dataset(self, dataset_id: str) -> Optional[EvaluationDataset]:
        return self.db.query(EvaluationDataset).filter(EvaluationDataset.id == dataset_id).first()

    def get_first_dataset(self) -> Optional[EvaluationDataset]:
        return self.db.query(EvaluationDataset).first()

    def list_datasets(self) -> List[EvaluationDataset]:
        return self.db.query(EvaluationDataset).order_by(EvaluationDataset.created_at.desc()).all()

    def create_dataset(self, name: str, description: Optional[str] = None) -> EvaluationDataset:
        ds = EvaluationDataset(name=name, description=description)
        self.db.add(ds)
        self.db.commit()
        self.db.refresh(ds)
        return ds

    # Questions
    def create_question(
        self,
        dataset_id: str,
        question: str,
        expected_answer: str,
        relevant_document_name: str,
        relevant_page: Optional[int],
        expected_supporting_context: str
    ) -> EvaluationQuestion:
        q = EvaluationQuestion(
            dataset_id=dataset_id,
            question=question,
            expected_answer=expected_answer,
            relevant_document_name=relevant_document_name,
            relevant_page=relevant_page,
            expected_supporting_context=expected_supporting_context
        )
        self.db.add(q)
        self.db.commit()
        self.db.refresh(q)
        return q

    def get_questions_for_dataset(self, dataset_id: str) -> List[EvaluationQuestion]:
        return self.db.query(EvaluationQuestion).filter(EvaluationQuestion.dataset_id == dataset_id).all()

    # Runs
    def create_run(self, dataset_id: str, name: str, config: Dict[str, Any]) -> EvaluationRun:
        run = EvaluationRun(
            dataset_id=dataset_id,
            name=name,
            config=config,
            status="PENDING"
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_run(self, run_id: str) -> Optional[EvaluationRun]:
        return self.db.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()

    def list_runs(self, limit: int = 20) -> List[EvaluationRun]:
        return (
            self.db.query(EvaluationRun)
            .order_by(EvaluationRun.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_latest_run(self) -> Optional[EvaluationRun]:
        return (
            self.db.query(EvaluationRun)
            .filter(EvaluationRun.status == "COMPLETED")
            .order_by(EvaluationRun.completed_at.desc())
            .first()
        )

    def update_run_status(self, run_id: str, status: str, error_message: Optional[str] = None) -> Optional[EvaluationRun]:
        run = self.get_run(run_id)
        if not run:
            return None
        run.status = status
        if error_message:
            run.error_message = error_message
        self.db.commit()
        self.db.refresh(run)
        return run

    def complete_run(
        self,
        run_id: str,
        total_questions: int,
        mean_recall_at_k: float,
        mean_mrr: float,
        mean_hit_rate_at_k: float,
        mean_faithfulness: float,
        mean_answer_correctness: float,
        mean_citation_correctness: float
    ) -> Optional[EvaluationRun]:
        run = self.get_run(run_id)
        if not run:
            return None
        run.status = "COMPLETED"
        run.total_questions = total_questions
        run.mean_recall_at_k = round(mean_recall_at_k, 4)
        run.mean_mrr = round(mean_mrr, 4)
        run.mean_hit_rate_at_k = round(mean_hit_rate_at_k, 4)
        run.mean_faithfulness = round(mean_faithfulness, 4)
        run.mean_answer_correctness = round(mean_answer_correctness, 4)
        run.mean_citation_correctness = round(mean_citation_correctness, 4)
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(run)
        return run

    # Results
    def create_result(
        self,
        run_id: str,
        question_id: Optional[str],
        question: str,
        generated_answer: str,
        retrieved_chunks: List[Any],
        citations: List[Any],
        recall_at_k: float,
        mrr: float,
        hit_rate_at_k: float,
        faithfulness_score: float,
        faithfulness_reason: Optional[str],
        answer_correctness_score: float,
        answer_correctness_reason: Optional[str],
        citation_correctness_score: float,
        citation_correctness_reason: Optional[str],
        execution_time_ms: float
    ) -> EvaluationResult:
        res = EvaluationResult(
            run_id=run_id,
            question_id=question_id,
            question=question,
            generated_answer=generated_answer,
            retrieved_chunks=retrieved_chunks,
            citations=citations,
            recall_at_k=round(recall_at_k, 4),
            mrr=round(mrr, 4),
            hit_rate_at_k=round(hit_rate_at_k, 4),
            faithfulness_score=round(faithfulness_score, 4),
            faithfulness_reason=faithfulness_reason,
            answer_correctness_score=round(answer_correctness_score, 4),
            answer_correctness_reason=answer_correctness_reason,
            citation_correctness_score=round(citation_correctness_score, 4),
            citation_correctness_reason=citation_correctness_reason,
            execution_time_ms=round(execution_time_ms, 2)
        )
        self.db.add(res)
        self.db.commit()
        self.db.refresh(res)
        return res

