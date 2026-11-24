import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SearchResponse, Document, ChunkSearchHit } from '../types';
import { 
  Search, 
  Filter, 
  Layers, 
  Sliders, 
  Clock, 
  FileText, 
  ArrowRight, 
  Hash, 
  Sparkles,
  CheckCircle2
} from 'lucide-react';

export const SearchExplorer: React.FC = () => {
  const [query, setQuery] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('all');
  const [topK, setTopK] = useState(6);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.35);
  
  const [loading, setLoading] = useState(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const docs = await api.listDocuments();
      setDocuments(docs.filter(d => d.status === 'COMPLETED'));
    } catch (e) {
      console.error(e);
    }
  };

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    try {
      setLoading(true);
      const docFilter = selectedDocId === 'all' ? undefined : [selectedDocId];
      const res = await api.search(query, topK, similarityThreshold, docFilter);
      setSearchResponse(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          Semantic Search Explorer
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Query the high-dimensional vector space directly. Inspect rank positions, cosine similarities, and retrieved passages.
        </p>
      </div>

      {/* Query Bar and Controls */}
      <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-5 shadow-sm space-y-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-3.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Enter natural-language query to evaluate vector cosine retrieval..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full rounded-xl border border-navy-700 bg-navy-950 py-3 pl-11 pr-4 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition disabled:opacity-50 flex items-center gap-2"
          >
            {loading ? <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Search className="h-4 w-4" />}
            <span>Retrieve</span>
          </button>
        </form>

        {/* Filters and Sliders */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-3 border-t border-navy-700/60 text-xs">
          {/* Document Filter */}
          <div>
            <label className="block text-slate-400 font-medium mb-1.5">Scope to Document:</label>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="w-full rounded-lg border border-navy-700 bg-navy-850 py-2 px-3 text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="all">All Documents ({documents.length})</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>{d.filename}</option>
              ))}
            </select>
          </div>

          {/* Top-K */}
          <div>
            <div className="flex justify-between font-medium mb-1.5">
              <span className="text-slate-400">Top-K Results:</span>
              <span className="text-indigo-400 font-mono">{topK} chunks</span>
            </div>
            <input
              type="range"
              min="1"
              max="20"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full accent-indigo-500 mt-2"
            />
          </div>

          {/* Similarity Threshold */}
          <div>
            <div className="flex justify-between font-medium mb-1.5">
              <span className="text-slate-400">Cosine Similarity Threshold:</span>
              <span className="text-indigo-400 font-mono">{similarityThreshold.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.90"
              step="0.05"
              value={similarityThreshold}
              onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
              className="w-full accent-indigo-500 mt-2"
            />
          </div>
        </div>
      </div>

      {/* Search Results Summary */}
      {searchResponse && (
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <div>
            Retrieved <span className="font-semibold text-white">{searchResponse.total_results}</span> passages matching query in <span className="font-mono text-indigo-400">{searchResponse.execution_time_ms} ms</span>
          </div>
          <div>
            Model: text-embedding-3-small (1536 dims)
          </div>
        </div>
      )}

      {/* Results List */}
      <div className="space-y-4">
        {searchResponse && searchResponse.results.length === 0 ? (
          <div className="rounded-2xl border border-navy-700 bg-navy-900/60 p-12 text-center text-slate-400">
            <Search className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-300">No Vector Matches Above Threshold</p>
            <p className="text-xs text-slate-500 mt-1">
              Try lowering the similarity threshold or phrasing the query differently.
            </p>
          </div>
        ) : (
          searchResponse?.results.map((hit, index) => {
            const pct = (hit.similarity_score * 100).toFixed(1);
            return (
              <div
                key={hit.id}
                className="rounded-2xl border border-navy-700/80 bg-navy-900/80 p-5 hover:border-indigo-500/50 transition shadow-sm"
              >
                <div className="flex items-center justify-between pb-3 mb-3 border-b border-navy-700/60 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-600 text-white font-mono font-bold text-xs">
                      #{index + 1}
                    </span>
                    <span className="font-semibold text-white flex items-center gap-1.5">
                      <FileText className="h-3.5 w-3.5 text-indigo-400" />
                      {hit.document_name}
                    </span>
                    <span className="rounded bg-navy-800 px-2 py-0.5 text-slate-300">
                      Page {hit.page_number}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-slate-400 font-mono text-[11px]">
                      {hit.token_count} tokens
                    </span>
                    <div className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-mono font-bold text-emerald-400">
                      <span>{pct}% Similarity</span>
                    </div>
                  </div>
                </div>

                <p className="text-sm text-slate-200 leading-relaxed font-normal whitespace-pre-wrap">
                  {hit.text}
                </p>

                <div className="mt-3 pt-2 text-[10px] text-slate-500 font-mono flex items-center justify-between">
                  <span>Chunk ID: {hit.id}</span>
                  <span>Chunk Index: #{hit.chunk_index}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
