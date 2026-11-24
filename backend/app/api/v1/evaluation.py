from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.common import APIResponse
from app.schemas.evaluation import (
    EvaluationDatasetRead,
    EvaluationRunConfig,
    EvaluationRunRead,
    EvaluationComparisonRequest,
    EvaluationComparisonResponse
)
from app.services.evaluation_service import EvaluationService
from app.repositories.evaluation_repo import EvaluationRepository

router = APIRouter(prefix="/evaluation", tags=["Evaluation Engine"])


@router.get("/dataset", response_model=APIResponse[EvaluationDatasetRead])
def get_benchmark_dataset(db: Session = Depends(get_db)):
    """Retrieves standard benchmark dataset with ground-truth QA pairs."""
    service = EvaluationService(db)
    dataset = service.ensure_default_benchmark_dataset()
    return APIResponse(
        success=True,
        message="Benchmark dataset retrieved.",
        data=EvaluationDatasetRead.model_validate(dataset)
    )


@router.post("/run", response_model=APIResponse[EvaluationRunRead])
def run_benchmark(
    config: EvaluationRunConfig,
    db: Session = Depends(get_db)
):
    """
    Executes actual benchmark evaluation across all dataset questions.
    Computes Recall@K, MRR, Hit Rate@K, Faithfulness, and Answer Correctness.
    """
    service = EvaluationService(db)
    run_read = service.run_benchmark(config)
    return APIResponse(
        success=True,
        message=f"Evaluation run '{run_read.name}' completed with {run_read.total_questions} questions.",
        data=run_read
    )


@router.get("/runs", response_model=APIResponse[List[EvaluationRunRead]])
def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists past evaluation benchmark runs."""
    repo = EvaluationRepository(db)
    runs = repo.list_runs(limit=limit)
    return APIResponse(
        success=True,
        message=f"Retrieved {len(runs)} evaluation runs.",
        data=[EvaluationRunRead.model_validate(r) for r in runs]
    )


@router.get("/runs/{run_id}", response_model=APIResponse[EvaluationRunRead])
def get_run(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full details and itemized results for an evaluation run."""
    repo = EvaluationRepository(db)
    run = repo.get_run(run_id)
    if not run:
        return APIResponse(success=False, message="Run not found", data=None)

    return APIResponse(
        success=True,
        message="Evaluation run loaded.",
        data=EvaluationRunRead.model_validate(run)
    )


@router.get("/latest", response_model=APIResponse[Optional[EvaluationRunRead]])
def get_latest_run(db: Session = Depends(get_db)):
    """Retrieves the most recent completed evaluation run."""
    repo = EvaluationRepository(db)
    run = repo.get_latest_run()
    if not run:
        return APIResponse(
            success=True,
            message="No completed evaluation runs found yet.",
            data=None
        )
    return APIResponse(
        success=True,
        message="Latest evaluation run retrieved.",
        data=EvaluationRunRead.model_validate(run)
    )


@router.post("/compare", response_model=APIResponse[EvaluationComparisonResponse])
def compare_runs(
    request: EvaluationComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compares two benchmark runs side-by-side to analyze the impact of
    different configurations (e.g. chunk size, top-K, similarity thresholds).
    """
    service = EvaluationService(db)
    comparison = service.compare_runs(request.run_id_a, request.run_id_b)
    return APIResponse(
        success=True,
        message="Comparison generated successfully.",
        data=comparison
    )

