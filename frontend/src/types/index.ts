export type DocumentStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';

export interface Document {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  status: DocumentStatus;
  error_message?: string | null;
  total_pages: number;
  total_chunks: number;
  content_hash?: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number: number;
  text: string;
  token_count: number;
  metadata_json?: Record<string, any>;
  created_at?: string;
}

export interface DocumentDetail extends Document {
  chunks: DocumentChunk[];
}

export interface ChunkSearchHit {
  id: string;
  document_id: string;
  document_name: string;
  chunk_index: number;
  page_number: number;
  text: string;
  similarity_score: number;
  token_count: number;
  metadata_json?: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: ChunkSearchHit[];
  execution_time_ms: number;
}

export interface Citation {
  source_document: string;
  document_id: string;
  page_number: number;
  excerpt: string;
  chunk_id: string;
  similarity_score: number;
}

export interface RAGResponse {
  answer: string;
  citations: Citation[];
  retrieved_chunks: ChunkSearchHit[];
  conversation_id: string;
  message_id: string;
  grounded: boolean;
  is_refusal: boolean;
  execution_time_ms: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations: Citation[];
  retrieved_chunks: ChunkSearchHit[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface EvaluationQuestion {
  id: string;
  dataset_id: string;
  question: string;
  expected_answer: string;
  relevant_document_name: string;
  relevant_page: number | null;
  expected_supporting_context: string;
}

export interface EvaluationDataset {
  id: string;
  name: string;
  description: string;
  questions: EvaluationQuestion[];
}

export interface EvaluationResult {
  id: string;
  run_id: string;
  question_id?: string;
  question: string;
  generated_answer: string;
  retrieved_chunks: any[];
  citations: any[];
  recall_at_k: number;
  mrr: number;
  hit_rate_at_k: number;
  faithfulness_score: number;
  faithfulness_reason?: string;
  answer_correctness_score: number;
  answer_correctness_reason?: string;
  citation_correctness_score: number;
  citation_correctness_reason?: string;
  execution_time_ms: number;
}

export interface EvaluationRun {
  id: string;
  dataset_id: string;
  name: string;
  config: {
    top_k?: number;
    similarity_threshold?: number;
    chunk_size?: number;
    chunk_overlap?: number;
    [key: string]: any;
  };
  status: string;
  error_message?: string | null;
  total_questions: number;
  mean_recall_at_k: number;
  mean_mrr: number;
  mean_hit_rate_at_k: number;
  mean_faithfulness: number;
  mean_answer_correctness: number;
  mean_citation_correctness: number;
  created_at: string;
  completed_at?: string | null;
  results?: EvaluationResult[];
}

export interface EvaluationComparison {
  run_a: EvaluationRun;
  run_b: EvaluationRun;
  metrics_delta: {
    recall_at_k_delta: number;
    mrr_delta: number;
    hit_rate_at_k_delta: number;
    faithfulness_delta: number;
    answer_correctness_delta: number;
    citation_correctness_delta: number;
  };
  summary_analysis: string;
}

export interface DashboardStats {
  total_documents: number;
  total_chunks: number;
  total_questions_asked: number;
  total_conversations: number;
  latest_evaluation: {
    id: string;
    name: string;
    completed_at: string;
    mean_recall_at_k: number;
    mean_mrr: number;
    mean_hit_rate_at_k: number;
    mean_faithfulness: number;
    mean_answer_correctness: number;
    mean_citation_correctness: number;
  } | null;
}
