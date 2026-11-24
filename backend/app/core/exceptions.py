from typing import Any, Optional


class TraceRAGException(Exception):
    def __init__(self, message: str, status_code: int = 400, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DocumentNotFoundException(TraceRAGException):
    def __init__(self, document_id: str):
        super().__init__(f"Document with ID '{document_id}' not found.", status_code=404)


class InvalidFileException(TraceRAGException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class DocumentProcessingException(TraceRAGException):
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(f"Document processing failed: {message}", status_code=422, details=details)


class EmbeddingException(TraceRAGException):
    def __init__(self, message: str):
        super().__init__(f"Embedding generation error: {message}", status_code=502)


class RetrievalException(TraceRAGException):
    def __init__(self, message: str):
        super().__init__(f"Retrieval error: {message}", status_code=500)


class GenerationException(TraceRAGException):
    def __init__(self, message: str):
        super().__init__(f"LLM Generation error: {message}", status_code=502)


class EvaluationException(TraceRAGException):
    def __init__(self, message: str):
        super().__init__(f"Evaluation benchmark error: {message}", status_code=500)

