import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  EvaluationRun, 
  EvaluationDataset, 
  EvaluationComparison, 
  EvaluationResult 
} from '../types';
import { 
  BarChart3, 
  Play, 
  Layers, 
  TrendingUp, 
  CheckCircle2, 
  GitCompare, 
  FileText, 
  HelpCircle, 
  ChevronDown, 
  ChevronUp, 
  Sparkles, 
  ShieldCheck, 
  AlertCircle,
  RefreshCw,
  Clock,
  ArrowRight
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Legend, 
  Cell 
} from 'recharts';

export const EvaluationLab: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'run' | 'compare' | 'dataset' | 'history'>('run');
  const [dataset, setDataset] = useState<EvaluationDataset | null>(null);
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [activeRun, setActiveRun] = useState<EvaluationRun | null>(null);
  const [running, setRunning] = useState(false);

  // Form config for new run
  const [runName, setRunName] = useState('Top-K=4 / Thresh=0.40 Benchmark');
  const [topK, setTopK] = useState(4);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.40);

  // Comparison State
  const [runIdA, setRunIdA] = useState<string>('');
  const [runIdB, setRunIdB] = useState<string>('');
  const [comparison, setComparison] = useState<EvaluationComparison | null>(null);
  const [comparing, setComparing] = useState(false);

  // Expanded questions in result list
  const [expandedResults, setExpandedResults] = useState<Record<string, boolean>>({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [ds, runList] = await Promise.all([
        api.getBenchmarkDataset(),
        api.listEvaluationRuns()
      ]);
      setDataset(ds);
      setRuns(runList);

      if (runList.length > 0) {
        // Load details for the most recent run
        const fullRun = await api.getEvaluationRun(runList[0].id);
        setActiveRun(fullRun);

        // Pre-populate comparison dropdowns if >= 2 runs
        setRunIdA(runList[0].id);
        if (runList.length > 1) {
          setRunIdB(runList[1].id);
        }
      }
    } catch (e) {
      console.error('Failed to load evaluation data:', e);
    }
  };

  const handleExecuteBenchmark = async () => {
    try {
      setRunning(true);
      const newRun = await api.runBenchmark({
        name: runName || `Benchmark (Top-K=${topK}, Thresh=${similarityThreshold})`,
        dataset_id: dataset?.id,
        top_k: topK,
        similarity_threshold: similarityThreshold
      });

      // Reload full run with results
      const fullRun = await api.getEvaluationRun(newRun.id);
      setActiveRun(fullRun);
      
      // Update runs list
      const updatedRuns = await api.listEvaluationRuns();
      setRuns(updatedRuns);

      if (updatedRuns.length >= 2) {
        setRunIdA(updatedRuns[0].id);
        setRunIdB(updatedRuns[1].id);
      }
    } catch (err: any) {
      alert(`Benchmark execution failed: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleCompare = async () => {
    if (!runIdA || !runIdB || runIdA === runIdB) {
      alert('Please select two distinct runs to compare.');
      return;
    }

    try {
      setComparing(true);
      const res = await api.compareRuns(runIdA, runIdB);
      setComparison(res);
    } catch (err: any) {
      alert(`Comparison failed: ${err.message}`);
    } finally {
      setComparing(false);
    }
  };

  const toggleExpand = (resId: string) => {
    setExpandedResults(prev => ({
      ...prev,
      [resId]: !prev[resId]
    }));
  };

  // Recharts data for active run
  const activeChartData = activeRun ? [
    { name: 'Recall@K', score: activeRun.mean_recall_at_k * 100, color: '#6366F1' },
    { name: 'MRR', score: activeRun.mean_mrr * 100, color: '#818CF8' },
    { name: 'Hit Rate@K', score: activeRun.mean_hit_rate_at_k * 100, color: '#38BDF8' },
    { name: 'Faithfulness', score: activeRun.mean_faithfulness * 100, color: '#10B981' },
    { name: 'Correctness', score: activeRun.mean_answer_correctness * 100, color: '#34D399' },
    { name: 'Citation Score', score: activeRun.mean_citation_correctness * 100, color: '#F59E0B' }
  ] : [];

  // Comparison Chart Data
  const comparisonChartData = comparison ? [
    {
      metric: 'Recall@K',
      [comparison.run_a.name]: comparison.run_a.mean_recall_at_k * 100,
      [comparison.run_b.name]: comparison.run_b.mean_recall_at_k * 100
    },
    {
      metric: 'MRR',
      [comparison.run_a.name]: comparison.run_a.mean_mrr * 100,
      [comparison.run_b.name]: comparison.run_b.mean_mrr * 100
    },
    {
      metric: 'Hit Rate@K',
      [comparison.run_a.name]: comparison.run_a.mean_hit_rate_at_k * 100,
      [comparison.run_b.name]: comparison.run_b.mean_hit_rate_at_k * 100
    },
    {
      metric: 'Faithfulness',
      [comparison.run_a.name]: comparison.run_a.mean_faithfulness * 100,
      [comparison.run_b.name]: comparison.run_b.mean_faithfulness * 100
    },
    {
      metric: 'Correctness',
      [comparison.run_a.name]: comparison.run_a.mean_answer_correctness * 100,
      [comparison.run_b.name]: comparison.run_b.mean_answer_correctness * 100
    },
    {
      metric: 'Citation Score',
      [comparison.run_a.name]: comparison.run_a.mean_citation_correctness * 100,
      [comparison.run_b.name]: comparison.run_b.mean_citation_correctness * 100
    }
  ] : [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            RAG Evaluation Lab
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Measure retrieval precision (Recall@K, MRR, Hit Rate@K) and generation grounding (Faithfulness, Correctness, Citations).
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex rounded-xl bg-navy-900 border border-navy-700/80 p-1 text-xs">
          <button
            onClick={() => setActiveTab('run')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'run' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Play className="h-3.5 w-3.5" />
            <span>Benchmark Run</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('compare');
              if (runs.length >= 2 && !comparison) handleCompare();
            }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'compare' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <GitCompare className="h-3.5 w-3.5" />
            <span>Compare Configs</span>
          </button>
          <button
            onClick={() => setActiveTab('dataset')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'dataset' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            <span>Dataset ({dataset?.questions.length || 0})</span>
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium transition ${
              activeTab === 'history' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Clock className="h-3.5 w-3.5" />
            <span>Runs ({runs.length})</span>
          </button>
        </div>
      </div>

      {/* TAB 1: RUN BENCHMARK */}
      {activeTab === 'run' && (
        <div className="space-y-8">
          {/* Runner Configuration Card */}
          <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-navy-700/60">
              <div>
                <h3 className="text-sm font-semibold text-white">Configure Benchmark Execution</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Runs all {dataset?.questions.length || 18} ground-truth questions against current vector index.
                </p>
              </div>
              <button
                onClick={handleExecuteBenchmark}
                disabled={running}
                className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition disabled:opacity-50"
              >
                {running ? (
                  <RefreshCw className="h-4 w-4 animate-spin text-white" />
                ) : (
                  <Play className="h-4 w-4 fill-white" />
                )}
                <span>{running ? 'Executing 18 Benchmark Questions...' : 'Start Benchmark Run'}</span>
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Run Label:</label>
                <input
                  type="text"
                  value={runName}
                  onChange={(e) => setRunName(e.target.value)}
                  className="w-full rounded-lg border border-navy-700 bg-navy-850 px-3 py-2 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1.5">
                  <span className="text-slate-300">Top-K Passages:</span>
                  <span className="text-indigo-400 font-mono">{topK}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={topK}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setTopK(val);
                    setRunName(`Top-K=${val} / Thresh=${similarityThreshold.toFixed(2)} Run`);
                  }}
                  className="w-full accent-indigo-500 mt-1"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs font-medium mb-1.5">
                  <span className="text-slate-300">Similarity Threshold:</span>
                  <span className="text-indigo-400 font-mono">{similarityThreshold.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.10"
                  max="0.80"
                  step="0.05"
                  value={similarityThreshold}
                  onChange={(e) => {
                    const val = Number(e.target.value);
                    setSimilarityThreshold(val);
                    setRunName(`Top-K=${topK} / Thresh=${val.toFixed(2)} Run`);
                  }}
                  className="w-full accent-indigo-500 mt-1"
                />
              </div>
            </div>
          </div>

          {/* Active Run Results Display */}
          {activeRun ? (
            <div className="space-y-8">
              {/* Metric Cards Row */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="rounded-xl border border-navy-700 bg-navy-900/80 p-4 text-center">
                  <p className="text-[11px] font-medium text-slate-400">Recall@K</p>
                  <p className="text-2xl font-bold text-indigo-400 mt-1">
                    {(activeRun.mean_recall_at_k * 100).toFixed(1)}%
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">Context Coverage</p>
                </div>

                <div className="rounded-xl border border-navy-700 bg-navy-900/80 p-4 text-center">
                  <p className="text-[11px] font-medium text-slate-400">MRR</p>
                  <p className="text-2xl font-bold text-indigo-300 mt-1">
                    {(activeRun.mean_mrr * 100).toFixed(1)}%
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">Reciprocal Rank</p>
                </div>

                <div className="rounded-xl border border-navy-700 bg-navy-900/80 p-4 text-center">
                  <p className="text-[11px] font-medium text-slate-400">Hit Rate@K</p>
                  <p className="text-2xl font-bold text-cyan-400 mt-1">
                    {(activeRun.mean_hit_rate_at_k * 100).toFixed(1)}%
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">Presence in Top-K</p>
                </div>

                <div className="rounded-xl border border-navy-700 bg-navy-900/80 p-4 text-center">
                  <p className="text-[11px] font-medium text-slate-400">Faithfulness</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">
                    {(activeRun.mean_faithfulness * 100).toFixed(1)}%
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">Context Grounding</p>
                </div>

                <div className="rounded-xl border border-navy-700 bg-navy-900/80 p-4 text-center">
                  <p className="text-[11px] font-medium text-slate-400">Correctness</p>
                  <p className="text-2xl font-bold text-teal-400 mt-1">
                    {(activeRun.mean_answer_correctness * 100).toFixed(1)}%
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">Factual Alignment</p>
                </div>

                <div className="rounded-xl border border-navy-700 bg-navy-900/80 p-4 text-center">
                  <p className="text-[11px] font-medium text-slate-400">Citations</p>
                  <p className="text-2xl font-bold text-amber-400 mt-1">
                    {(activeRun.mean_citation_correctness * 100).toFixed(1)}%
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">Source Verification</p>
                </div>
              </div>

              {/* Chart Breakdown */}
              <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-6 shadow-sm">
                <h3 className="text-sm font-semibold text-white mb-4">
                  Benchmark Run Metrics: {activeRun.name}
                </h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={activeChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                      <XAxis dataKey="name" stroke="#64748B" fontSize={11} tickLine={false} />
                      <YAxis domain={[0, 100]} stroke="#64748B" fontSize={11} tickLine={false} unit="%" />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                        formatter={(val: any) => [`${Number(val).toFixed(1)}%`, 'Score']}
                      />
                      <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={50}>
                        {activeChartData.map((e, idx) => (
                          <Cell key={`cell-${idx}`} fill={e.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Itemized Questions Results */}
              <div className="rounded-2xl border border-navy-700 bg-navy-900/80 overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-navy-700/60 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white">
                      Itemized Question Evaluations ({activeRun.results?.length || 0})
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Inspect individual queries, retrieved hits, generated answers, citations, and evaluation reasoning.
                    </p>
                  </div>
                </div>

                <div className="divide-y divide-navy-700/50">
                  {activeRun.results?.map((res, idx) => {
                    const isExpanded = expandedResults[res.id];
                    return (
                      <div key={res.id} className="p-4 hover:bg-navy-850/40 transition">
                        <div 
                          onClick={() => toggleExpand(res.id)}
                          className="flex items-center justify-between cursor-pointer"
                        >
                          <div className="flex items-center gap-3 pr-4">
                            <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-navy-800 text-indigo-400 font-mono text-xs font-semibold">
                              #{idx + 1}
                            </span>
                            <span className="text-xs font-medium text-white">{res.question}</span>
                          </div>

                          <div className="flex items-center gap-4 flex-shrink-0 text-xs font-mono">
                            <span className="text-indigo-400">Recall: {(res.recall_at_k * 100).toFixed(0)}%</span>
                            <span className="text-emerald-400">Faith: {(res.faithfulness_score * 100).toFixed(0)}%</span>
                            <span className="text-teal-400">Corr: {(res.answer_correctness_score * 100).toFixed(0)}%</span>
                            {isExpanded ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                          </div>
                        </div>

                        {/* Expanded details */}
                        {isExpanded && (
                          <div className="mt-4 pt-3 border-t border-navy-700/60 space-y-3 text-xs">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="rounded-xl border border-navy-700 bg-navy-950 p-3">
                                <span className="font-semibold text-slate-400 block mb-1">Generated Answer:</span>
                                <p className="text-slate-200">{res.generated_answer}</p>
                              </div>

                              <div className="rounded-xl border border-navy-700 bg-navy-950 p-3">
                                <span className="font-semibold text-slate-400 block mb-1">Faithfulness Reason:</span>
                                <p className="text-emerald-300/90">{res.faithfulness_reason}</p>
                                <span className="font-semibold text-slate-400 block mt-2 mb-1">Correctness Reason:</span>
                                <p className="text-teal-300/90">{res.answer_correctness_reason}</p>
                              </div>
                            </div>

                            <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono pt-1">
                              <span>MRR: {res.mrr.toFixed(2)} | Hit Rate: {res.hit_rate_at_k.toFixed(1)}</span>
                              <span>Execution: {res.execution_time_ms} ms</span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-navy-700 p-12 text-center text-slate-400">
              <BarChart3 className="h-10 w-10 text-slate-600 mx-auto mb-2" />
              <p className="text-sm font-semibold text-white">No Active Run Selected</p>
              <p className="text-xs text-slate-500 mt-1">
                Click "Start Benchmark Run" above to execute evaluation against the 18 question benchmark dataset.
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: CONFIGURATION COMPARISON */}
      {activeTab === 'compare' && (
        <div className="space-y-8">
          {/* Comparison Selector Card */}
          <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-6 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-white">Compare Two Retrieval Configurations</h3>
            <p className="text-xs text-slate-400">
              Select two past benchmark executions to evaluate the impact of top-K, similarity thresholds, and chunking strategies.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Configuration A (Baseline):</label>
                <select
                  value={runIdA}
                  onChange={(e) => setRunIdA(e.target.value)}
                  className="w-full rounded-lg border border-navy-700 bg-navy-850 p-2.5 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                >
                  {runs.map(r => (
                    <option key={r.id} value={r.id}>
                      {r.name} (Top-K={r.config?.top_k}, Thresh={r.config?.similarity_threshold})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Configuration B (Experiment):</label>
                <select
                  value={runIdB}
                  onChange={(e) => setRunIdB(e.target.value)}
                  className="w-full rounded-lg border border-navy-700 bg-navy-850 p-2.5 text-xs text-slate-100 focus:border-indigo-500 focus:outline-none"
                >
                  {runs.map(r => (
                    <option key={r.id} value={r.id}>
                      {r.name} (Top-K={r.config?.top_k}, Thresh={r.config?.similarity_threshold})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="pt-2">
              <button
                onClick={handleCompare}
                disabled={comparing || runs.length < 2}
                className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition disabled:opacity-50"
              >
                <GitCompare className="h-4 w-4" />
                <span>{comparing ? 'Analyzing Deltas...' : 'Run Comparative Analysis'}</span>
              </button>
            </div>
          </div>

          {/* Comparison Output */}
          {comparison ? (
            <div className="space-y-8">
              {/* Delta Summary Table */}
              <div className="rounded-2xl border border-navy-700 bg-navy-900/80 overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-navy-700/60">
                  <h3 className="text-sm font-semibold text-white">Side-by-Side Metric Deltas</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-navy-850/80 text-slate-400 font-medium uppercase tracking-wider border-b border-navy-700/60">
                      <tr>
                        <th className="py-3 px-6">Metric</th>
                        <th className="py-3 px-6">{comparison.run_a.name} (A)</th>
                        <th className="py-3 px-6">{comparison.run_b.name} (B)</th>
                        <th className="py-3 px-6">Delta (B - A)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-navy-700/50 text-slate-300 font-mono">
                      {[
                        { label: 'Recall@K', a: comparison.run_a.mean_recall_at_k, b: comparison.run_b.mean_recall_at_k, d: comparison.metrics_delta.recall_at_k_delta },
                        { label: 'Mean Reciprocal Rank (MRR)', a: comparison.run_a.mean_mrr, b: comparison.run_b.mean_mrr, d: comparison.metrics_delta.mrr_delta },
                        { label: 'Hit Rate@K', a: comparison.run_a.mean_hit_rate_at_k, b: comparison.run_b.mean_hit_rate_at_k, d: comparison.metrics_delta.hit_rate_at_k_delta },
                        { label: 'Faithfulness', a: comparison.run_a.mean_faithfulness, b: comparison.run_b.mean_faithfulness, d: comparison.metrics_delta.faithfulness_delta },
                        { label: 'Answer Correctness', a: comparison.run_a.mean_answer_correctness, b: comparison.run_b.mean_answer_correctness, d: comparison.metrics_delta.answer_correctness_delta },
                        { label: 'Citation Correctness', a: comparison.run_a.mean_citation_correctness, b: comparison.run_b.mean_citation_correctness, d: comparison.metrics_delta.citation_correctness_delta }
                      ].map((m, i) => {
                        const isPositive = m.d > 0;
                        const isZero = m.d === 0;
                        return (
                          <tr key={i} className="hover:bg-navy-850/50">
                            <td className="py-3 px-6 font-sans font-medium text-white">{m.label}</td>
                            <td className="py-3 px-6">{(m.a * 100).toFixed(1)}%</td>
                            <td className="py-3 px-6">{(m.b * 100).toFixed(1)}%</td>
                            <td className="py-3 px-6">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded font-bold ${
                                isZero 
                                  ? 'bg-navy-700 text-slate-400' 
                                  : isPositive 
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              }`}>
                                {isPositive ? '+' : ''}{(m.d * 100).toFixed(1)}%
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Side-by-Side Bar Chart */}
              <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-6 shadow-sm">
                <h3 className="text-sm font-semibold text-white mb-4">Comparative Quality Distribution</h3>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={comparisonChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
                      <XAxis dataKey="metric" stroke="#64748B" fontSize={11} tickLine={false} />
                      <YAxis domain={[0, 100]} stroke="#64748B" fontSize={11} tickLine={false} unit="%" />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
                        formatter={(val: any) => [`${Number(val).toFixed(1)}%`]}
                      />
                      <Legend />
                      <Bar dataKey={comparison.run_a.name} fill="#6366F1" radius={[4, 4, 0, 0]} maxBarSize={30} />
                      <Bar dataKey={comparison.run_b.name} fill="#38BDF8" radius={[4, 4, 0, 0]} maxBarSize={30} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Qualitative Analysis Report */}
              <div className="rounded-2xl border border-navy-700 bg-navy-900/80 p-6 shadow-sm space-y-3">
                <div className="flex items-center gap-2 text-indigo-400">
                  <Sparkles className="h-4 w-4" />
                  <h3 className="text-sm font-semibold text-white">Comparative Evaluation Synthesis</h3>
                </div>
                <div className="rounded-xl border border-navy-700/80 bg-navy-950 p-4 text-xs font-mono text-slate-300 leading-relaxed whitespace-pre-wrap">
                  {comparison.summary_analysis}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-navy-700 p-12 text-center text-slate-400">
              <GitCompare className="h-10 w-10 text-slate-600 mx-auto mb-2" />
              <p className="text-sm font-semibold text-white">Select Two Runs Above</p>
              <p className="text-xs text-slate-500 mt-1">
                Compare different Top-K values or similarity thresholds to observe metric trade-offs.
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: DATASET EXPLORER */}
      {activeTab === 'dataset' && (
        <div className="rounded-2xl border border-navy-700 bg-navy-900/80 overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-navy-700/60 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">{dataset?.name || 'TraceRAG Benchmark'}</h3>
              <p className="text-xs text-slate-400 mt-0.5">{dataset?.description}</p>
            </div>
            <span className="rounded bg-indigo-500/10 px-2.5 py-1 text-xs font-semibold text-indigo-400 border border-indigo-500/20">
              {dataset?.questions.length || 0} Ground Truth Records
            </span>
          </div>

          <div className="divide-y divide-navy-700/50">
            {dataset?.questions.map((q, idx) => (
              <div key={q.id} className="p-4 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-indigo-400">Q{idx + 1}.</span>
                    <span className="font-semibold text-white text-sm">{q.question}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-navy-800 px-2 py-0.5 text-slate-300 font-mono text-[11px]">
                      {q.relevant_document_name}
                    </span>
                    {q.relevant_page && (
                      <span className="rounded bg-navy-800 px-2 py-0.5 text-indigo-400 font-mono text-[11px]">
                        Page {q.relevant_page}
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                  <div className="p-2.5 rounded-lg bg-navy-950 border border-navy-800">
                    <span className="text-[10px] uppercase font-semibold text-slate-500 block mb-1">
                      Expected Ground Truth Answer:
                    </span>
                    <p className="text-slate-200">{q.expected_answer}</p>
                  </div>
                  <div className="p-2.5 rounded-lg bg-navy-950 border border-navy-800">
                    <span className="text-[10px] uppercase font-semibold text-slate-500 block mb-1">
                      Expected Supporting Context Excerpt:
                    </span>
                    <p className="text-slate-300 italic">"{q.expected_supporting_context}"</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: HISTORY */}
      {activeTab === 'history' && (
        <div className="rounded-2xl border border-navy-700 bg-navy-900/80 overflow-hidden shadow-sm">
          <div className="px-6 py-4 border-b border-navy-700/60">
            <h3 className="text-sm font-semibold text-white">Benchmark Runs Execution History</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-850/80 text-slate-400 font-medium uppercase tracking-wider border-b border-navy-700/60">
                <tr>
                  <th className="py-3 px-6">Run Name</th>
                  <th className="py-3 px-6">Parameters</th>
                  <th className="py-3 px-6">Recall@K</th>
                  <th className="py-3 px-6">MRR</th>
                  <th className="py-3 px-6">Faithfulness</th>
                  <th className="py-3 px-6">Correctness</th>
                  <th className="py-3 px-6">Date</th>
                  <th className="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-700/50 text-slate-300 font-mono">
                {runs.map((r) => (
                  <tr key={r.id} className="hover:bg-navy-850/50">
                    <td className="py-3.5 px-6 font-sans font-medium text-white">{r.name}</td>
                    <td className="py-3.5 px-6 text-slate-400">
                      Top-K: {r.config?.top_k}, Thresh: {r.config?.similarity_threshold}
                    </td>
                    <td className="py-3.5 px-6 text-indigo-400 font-bold">
                      {(r.mean_recall_at_k * 100).toFixed(1)}%
                    </td>
                    <td className="py-3.5 px-6 text-indigo-300">
                      {(r.mean_mrr * 100).toFixed(1)}%
                    </td>
                    <td className="py-3.5 px-6 text-emerald-400">
                      {(r.mean_faithfulness * 100).toFixed(1)}%
                    </td>
                    <td className="py-3.5 px-6 text-teal-400">
                      {(r.mean_answer_correctness * 100).toFixed(1)}%
                    </td>
                    <td className="py-3.5 px-6 text-slate-500 font-sans text-[11px]">
                      {new Date(r.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="py-3.5 px-6 text-right font-sans">
                      <button
                        onClick={async () => {
                          const full = await api.getEvaluationRun(r.id);
                          setActiveRun(full);
                          setActiveTab('run');
                        }}
                        className="rounded-lg border border-navy-700 bg-navy-800 px-3 py-1 text-slate-200 hover:text-white hover:border-indigo-500"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

