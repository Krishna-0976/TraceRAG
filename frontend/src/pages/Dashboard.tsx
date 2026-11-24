import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DashboardStats, Document, EvaluationRun } from '../types';
import { PageId } from '../components/Navbar';
import { 
  FileText, 
  Layers, 
  MessageSquare, 
  CheckCircle2, 
  TrendingUp, 
  ArrowUpRight, 
  ShieldAlert, 
  Sparkles,
  Search,
  BarChart3,
  RefreshCw
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell 
} from 'recharts';

interface DashboardProps {
  setActivePage: (page: PageId) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ setActivePage }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentDocs, setRecentDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setRefreshing(true);
      const [statsData, docsData] = await Promise.all([
        api.getDashboardStats(),
        api.listDocuments()
      ]);
      setStats(statsData);
      setRecentDocs(docsData.slice(0, 5));
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const latestEval = stats?.latest_evaluation;

  const evalChartData = latestEval ? [
    { name: 'Recall@K', score: latestEval.mean_recall_at_k * 100, color: '#6366F1' },
    { name: 'MRR', score: latestEval.mean_mrr * 100, color: '#818CF8' },
    { name: 'Hit Rate@K', score: latestEval.mean_hit_rate_at_k * 100, color: '#38BDF8' },
    { name: 'Faithfulness', score: latestEval.mean_faithfulness * 100, color: '#10B981' },
    { name: 'Correctness', score: latestEval.mean_answer_correctness * 100, color: '#34D399' },
    { name: 'Citations', score: latestEval.mean_citation_correctness * 100, color: '#F59E0B' }
  ] : [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Knowledge Engine Overview
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Real-time telemetry, vector indexing status, and grounded RAG benchmark quality.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDashboardData}
            disabled={refreshing}
            className="flex items-center gap-2 rounded-lg border border-navy-700 bg-navy-850 px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-navy-800 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin text-indigo-400' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setActivePage('workspace')}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition"
          >
            <Sparkles className="h-4 w-4" />
            Launch AI Workspace
          </button>
        </div>
      </div>

      {/* Metric Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Documents */}
        <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Documents</span>
            <div className="rounded-xl bg-indigo-500/10 p-2 text-indigo-400 border border-indigo-500/20">
              <FileText className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">
              {stats?.total_documents ?? 0}
            </span>
            <span className="text-xs text-slate-400">PDFs ingested</span>
          </div>
          <div className="mt-3 flex items-center text-xs text-indigo-400 font-medium">
            <span>Verified in PostgreSQL</span>
          </div>
        </div>

        {/* Total Indexed Chunks */}
        <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Indexed Chunks</span>
            <div className="rounded-xl bg-cyan-500/10 p-2 text-cyan-400 border border-cyan-500/20">
              <Layers className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">
              {stats?.total_chunks ?? 0}
            </span>
            <span className="text-xs text-slate-400">vector embeddings</span>
          </div>
          <div className="mt-3 flex items-center text-xs text-cyan-400 font-medium">
            <span>1536-dimensional vectors</span>
          </div>
        </div>

        {/* Total Questions Asked */}
        <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Questions Answered</span>
            <div className="rounded-xl bg-emerald-500/10 p-2 text-emerald-400 border border-emerald-500/20">
              <MessageSquare className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">
              {stats?.total_questions_asked ?? 0}
            </span>
            <span className="text-xs text-slate-400">messages</span>
          </div>
          <div className="mt-3 flex items-center text-xs text-emerald-400 font-medium">
            <span>100% Grounded Citations</span>
          </div>
        </div>

        {/* Evaluation Quality Score */}
        <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Mean Faithfulness</span>
            <div className="rounded-xl bg-amber-500/10 p-2 text-amber-400 border border-amber-500/20">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>
          <div className="mt-4 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight text-white">
              {latestEval ? `${(latestEval.mean_faithfulness * 100).toFixed(1)}%` : 'N/A'}
            </span>
            <span className="text-xs text-slate-400">benchmark rating</span>
          </div>
          <div className="mt-3 flex items-center text-xs text-amber-400 font-medium">
            <span>{latestEval ? 'Based on latest run' : 'Run benchmark in Lab'}</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Evaluation Breakdown & Quick Actions */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Evaluation Metrics Visualization */}
        <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-6 lg:col-span-2 shadow-sm">
          <div className="flex items-center justify-between border-b border-navy-700/60 pb-4">
            <div>
              <h2 className="text-base font-semibold text-white">
                RAG Benchmark Performance Radar
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {latestEval 
                  ? `Run: ${latestEval.name} (Calculated from actual benchmark executions)`
                  : 'No benchmark execution recorded yet. Run tests in the Evaluation Lab.'}
              </p>
            </div>
            <button
              onClick={() => setActivePage('evaluation')}
              className="flex items-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition"
            >
              Open Evaluation Lab <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="mt-6 h-64 w-full">
            {evalChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={evalChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748B" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#64748B" fontSize={11} tickLine={false} unit="%" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                    formatter={(value: any) => [`${Number(value).toFixed(1)}%`, 'Score']}
                  />
                  <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={48}>
                    {evalChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-center p-6 border border-dashed border-navy-700 rounded-xl">
                <BarChart3 className="h-10 w-10 text-slate-500 mb-2" />
                <p className="text-sm font-medium text-slate-300">No Benchmark Executions Yet</p>
                <p className="text-xs text-slate-500 mt-1 max-w-sm">
                  Run the 18-question benchmark in the Evaluation Lab to measure Recall@K, MRR, Faithfulness, and Answer Correctness.
                </p>
                <button
                  onClick={() => setActivePage('evaluation')}
                  className="mt-4 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-indigo-500"
                >
                  Run Benchmark Now
                </button>
              </div>
            )}
          </div>

          {/* Quick Metrics Ticker */}
          {latestEval && (
            <div className="mt-6 grid grid-cols-3 sm:grid-cols-6 gap-2 pt-4 border-t border-navy-700/60 text-center">
              <div>
                <p className="text-[10px] text-slate-400 font-medium">Recall@K</p>
                <p className="text-sm font-bold text-indigo-400 mt-0.5">
                  {(latestEval.mean_recall_at_k * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400 font-medium">MRR</p>
                <p className="text-sm font-bold text-indigo-300 mt-0.5">
                  {(latestEval.mean_mrr * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400 font-medium">Hit Rate@K</p>
                <p className="text-sm font-bold text-cyan-400 mt-0.5">
                  {(latestEval.mean_hit_rate_at_k * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400 font-medium">Faithfulness</p>
                <p className="text-sm font-bold text-emerald-400 mt-0.5">
                  {(latestEval.mean_faithfulness * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400 font-medium">Correctness</p>
                <p className="text-sm font-bold text-teal-400 mt-0.5">
                  {(latestEval.mean_answer_correctness * 100).toFixed(1)}%
                </p>
              </div>
              <div>
                <p className="text-[10px] text-slate-400 font-medium">Citations</p>
                <p className="text-sm font-bold text-amber-400 mt-0.5">
                  {(latestEval.mean_citation_correctness * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Quick Launch & Recent Docs */}
        <div className="space-y-6">
          {/* Quick Modules */}
          <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-5 space-y-3">
            <h3 className="text-sm font-semibold text-white">Platform Modules</h3>
            <div className="space-y-2">
              <button
                onClick={() => setActivePage('knowledge')}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-navy-700/60 bg-navy-850 hover:border-indigo-500/50 hover:bg-navy-800 transition text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-indigo-500/10 p-2 text-indigo-400">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-200">Knowledge Base</h4>
                    <p className="text-[11px] text-slate-400">Upload & chunk PDF documents</p>
                  </div>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-500" />
              </button>

              <button
                onClick={() => setActivePage('workspace')}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-navy-700/60 bg-navy-850 hover:border-indigo-500/50 hover:bg-navy-800 transition text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-emerald-500/10 p-2 text-emerald-400">
                    <Sparkles className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-200">AI Workspace</h4>
                    <p className="text-[11px] text-slate-400">Ask questions with strict citations</p>
                  </div>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-500" />
              </button>

              <button
                onClick={() => setActivePage('search')}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-navy-700/60 bg-navy-850 hover:border-indigo-500/50 hover:bg-navy-800 transition text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-cyan-500/10 p-2 text-cyan-400">
                    <Search className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-200">Search Explorer</h4>
                    <p className="text-[11px] text-slate-400">Interactive vector cosine search</p>
                  </div>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-500" />
              </button>

              <button
                onClick={() => setActivePage('evaluation')}
                className="w-full flex items-center justify-between p-3 rounded-xl border border-navy-700/60 bg-navy-850 hover:border-indigo-500/50 hover:bg-navy-800 transition text-left"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-amber-500/10 p-2 text-amber-400">
                    <BarChart3 className="h-4 w-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-200">Evaluation Lab</h4>
                    <p className="text-[11px] text-slate-400">Benchmark Recall@K, MRR & deltas</p>
                  </div>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-500" />
              </button>
            </div>
          </div>

          {/* Recent Ingested Documents */}
          <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white">Recent Documents</h3>
              <button
                onClick={() => setActivePage('knowledge')}
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                View all
              </button>
            </div>

            {recentDocs.length === 0 ? (
              <p className="text-xs text-slate-500 py-3 text-center">No documents uploaded yet.</p>
            ) : (
              <div className="space-y-2">
                {recentDocs.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between p-2.5 rounded-lg bg-navy-850 border border-navy-700/50 text-xs"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <FileText className="h-3.5 w-3.5 text-indigo-400 flex-shrink-0" />
                      <span className="font-medium text-slate-200 truncate">{doc.filename}</span>
                    </div>
                    <span className="rounded bg-navy-700 px-1.5 py-0.5 text-[10px] text-slate-300 font-mono">
                      {doc.total_chunks} ch
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

