import {
  Document,
  DocumentDetail,
  SearchResponse,
  RAGResponse,
  Conversation,
  EvaluationDataset,
  EvaluationRun,
  EvaluationComparison,
  DashboardStats
} from '../types';

const API_BASE = '/api/v1';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Accept': 'application/json',
      ...(options?.headers || {})
    }
  });

  const json = await response.json().catch(() => ({ success: false, message: 'Invalid JSON response from server' }));

  if (!response.ok || json.success === false) {
    const errorMsg = json.message || `HTTP ${response.status}: ${response.statusText}`;
    throw new Error(errorMsg);
  }

  return json.data as T;
}

export const api = {
  // Dashboard Stats
  async getDashboardStats(): Promise<DashboardStats> {
    return request<DashboardStats>('/stats');
  },

  // Documents
  async listDocuments(): Promise<Document[]> {
    return request<Document[]>('/documents');
  },

  async getDocument(documentId: string): Promise<DocumentDetail> {
    return request<DocumentDetail>(`/documents/${documentId}`);
  },

  async uploadDocument(
    file: File,
    chunkSize: number = 500,
    chunkOverlap: number = 100
  ): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('chunk_size', chunkSize.toString());
    formData.append('chunk_overlap', chunkOverlap.toString());

    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData
    });

    const json = await response.json();
    if (!response.ok || json.success === false) {
      throw new Error(json.message || 'Upload failed');
    }
    return json.data as Document;
  },

  async deleteDocument(documentId: string): Promise<boolean> {
    return request<boolean>(`/documents/${documentId}`, {
      method: 'DELETE'
    });
  },

  // Semantic Search
  async search(
    query: string,
    topK: number = 4,
    similarityThreshold: number = 0.40,
    documentIds?: string[]
  ): Promise<SearchResponse> {
    return request<SearchResponse>('/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        top_k: topK,
        similarity_threshold: similarityThreshold,
        document_ids: documentIds && documentIds.length > 0 ? documentIds : undefined
      })
    });
  },

  // RAG QA
  async queryRAG(
    query: string,
    conversationId?: string,
    topK: number = 4,
    similarityThreshold: number = 0.40,
    documentIds?: string[]
  ): Promise<RAGResponse> {
    return request<RAGResponse>('/rag/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        conversation_id: conversationId || undefined,
        top_k: topK,
        similarity_threshold: similarityThreshold,
        document_ids: documentIds && documentIds.length > 0 ? documentIds : undefined
      })
    });
  },

  // Conversations
  async listConversations(): Promise<Conversation[]> {
    return request<Conversation[]>('/conversations');
  },

  async getConversation(id: string): Promise<Conversation> {
    return request<Conversation>(`/conversations/${id}`);
  },

  async deleteConversation(id: string): Promise<boolean> {
    return request<boolean>(`/conversations/${id}`, {
      method: 'DELETE'
    });
  },

  // Evaluation
  async getBenchmarkDataset(): Promise<EvaluationDataset> {
    return request<EvaluationDataset>('/evaluation/dataset');
  },

  async runBenchmark(config: {
    name?: string;
    dataset_id?: string;
    top_k: number;
    similarity_threshold: number;
    chunk_size?: number;
    chunk_overlap?: number;
  }): Promise<EvaluationRun> {
    return request<EvaluationRun>('/evaluation/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
  },

  async listEvaluationRuns(): Promise<EvaluationRun[]> {
    return request<EvaluationRun[]>('/evaluation/runs');
  },

  async getEvaluationRun(runId: string): Promise<EvaluationRun> {
    return request<EvaluationRun>(`/evaluation/runs/${runId}`);
  },

  async getLatestEvaluationRun(): Promise<EvaluationRun | null> {
    return request<EvaluationRun | null>('/evaluation/latest');
  },

  async compareRuns(runIdA: string, runIdB: string): Promise<EvaluationComparison> {
    return request<EvaluationComparison>('/evaluation/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ run_id_a: runIdA, run_id_b: runIdB })
    });
  }
};
