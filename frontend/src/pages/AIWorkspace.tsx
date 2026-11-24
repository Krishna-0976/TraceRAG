import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { Conversation, Message, Document, Citation, ChunkSearchHit } from '../types';
import { CitationBadge } from '../components/CitationBadge';
import { 
  Send, 
  Sparkles, 
  Bot, 
  User, 
  Plus, 
  Trash2, 
  Layers, 
  ShieldCheck, 
  ShieldAlert, 
  Sliders, 
  Clock, 
  FileText,
  ChevronRight,
  MessageSquare,
  HelpCircle
} from 'lucide-react';

export const AIWorkspace: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('all');

  // Retrieval Settings
  const [topK, setTopK] = useState(4);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.40);
  const [showSettings, setShowSettings] = useState(false);

  // Inspector Drawer for active retrieved chunks
  const [inspectChunks, setInspectChunks] = useState<ChunkSearchHit[]>([]);
  const [showChunkDrawer, setShowChunkDrawer] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Initial load
  useEffect(() => {
    loadConversations();
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

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
      if (convs.length > 0 && !activeConvId) {
        selectConversation(convs[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const selectConversation = async (convId: string) => {
    try {
      setActiveConvId(convId);
      const detail = await api.getConversation(convId);
      setMessages(detail.messages || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewConversation = () => {
    setActiveConvId(null);
    setMessages([]);
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.deleteConversation(convId);
      const updated = conversations.filter(c => c.id !== convId);
      setConversations(updated);
      if (activeConvId === convId) {
        if (updated.length > 0) {
          selectConversation(updated[0].id);
        } else {
          handleNewConversation();
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || loading) return;

    // Optimistically add user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: activeConvId || '',
      role: 'user',
      content: query,
      citations: [],
      retrieved_chunks: [],
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, tempUserMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const docFilter = selectedDocId === 'all' ? undefined : [selectedDocId];
      const res = await api.queryRAG(
        query,
        activeConvId || undefined,
        topK,
        similarityThreshold,
        docFilter
      );

      const assistantMsg: Message = {
        id: res.message_id,
        conversation_id: res.conversation_id,
        role: 'assistant',
        content: res.answer,
        citations: res.citations,
        retrieved_chunks: res.retrieved_chunks,
        created_at: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMsg]);
      setActiveConvId(res.conversation_id);
      setInspectChunks(res.retrieved_chunks);

      // Refresh conversations list to update title and ordering
      loadConversations();
    } catch (err: any) {
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        conversation_id: activeConvId || '',
        role: 'assistant',
        content: `Error generating response: ${err.message || 'System failed to process query.'}`,
        citations: [],
        retrieved_chunks: [],
        created_at: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
      {/* Sidebar: Conversation Threads */}
      <aside className="w-72 flex-shrink-0 border-r border-navy-700/60 bg-navy-900/90 flex flex-col justify-between">
        <div className="p-4 border-b border-navy-700/60">
          <button
            onClick={handleNewConversation}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 hover:bg-indigo-500 transition"
          >
            <Plus className="h-4 w-4" />
            New Conversation
          </button>
        </div>

        {/* Thread List */}
        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 px-3 py-1">
            History Threads ({conversations.length})
          </div>
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">
              No conversation history yet.
            </div>
          ) : (
            conversations.map((conv) => {
              const isSelected = activeConvId === conv.id;
              return (
                <div
                  key={conv.id}
                  onClick={() => selectConversation(conv.id)}
                  className={`group flex items-center justify-between rounded-xl px-3 py-2 text-xs font-medium cursor-pointer transition ${
                    isSelected
                      ? 'bg-navy-800 text-white border border-indigo-500/40'
                      : 'text-slate-400 hover:bg-navy-850 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <MessageSquare className={`h-3.5 w-3.5 flex-shrink-0 ${isSelected ? 'text-indigo-400' : 'text-slate-500'}`} />
                    <span className="truncate">{conv.title}</span>
                  </div>
                  <button
                    onClick={(e) => handleDeleteConversation(conv.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition"
                    title="Delete Thread"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Workspace Quick Info */}
        <div className="p-4 border-t border-navy-700/60 bg-navy-950/60 text-xs text-slate-400 space-y-2">
          <div className="flex items-center justify-between">
            <span>Indexed Documents</span>
            <span className="font-semibold text-white">{documents.length}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Grounding Policy</span>
            <span className="text-emerald-400 font-medium">Strict No-Hallucination</span>
          </div>
        </div>
      </aside>

      {/* Main Chat Panel */}
      <main className="flex-1 flex flex-col bg-navy-950 overflow-hidden">
        {/* Top Control Bar */}
        <div className="flex items-center justify-between border-b border-navy-700/60 bg-navy-900/60 px-6 py-3">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400 font-medium">Filter Document Scope:</span>
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="rounded-lg border border-navy-700 bg-navy-850 py-1 px-3 text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              <option value="all">All Documents ({documents.length})</option>
              {documents.map((d) => (
                <option key={d.id} value={d.id}>{d.filename}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                showSettings 
                  ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300' 
                  : 'border-navy-700 bg-navy-850 text-slate-400 hover:text-white'
              }`}
            >
              <Sliders className="h-3.5 w-3.5" />
              <span>Retrieval: Top-{topK} (Thresh: {similarityThreshold})</span>
            </button>
          </div>
        </div>

        {/* Retrieval Parameter Sliders Drawer */}
        {showSettings && (
          <div className="grid grid-cols-2 gap-6 p-4 border-b border-navy-700/60 bg-navy-900/90 text-xs">
            <div>
              <div className="flex justify-between font-medium mb-1">
                <span className="text-slate-300">Top-K Passages:</span>
                <span className="text-indigo-400 font-mono">{topK}</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
            <div>
              <div className="flex justify-between font-medium mb-1">
                <span className="text-slate-300">Similarity Threshold:</span>
                <span className="text-indigo-400 font-mono">{similarityThreshold.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0.10"
                max="0.90"
                step="0.05"
                value={similarityThreshold}
                onChange={(e) => setSimilarityThreshold(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>
          </div>
        )}

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-lg mx-auto py-12">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-4">
                <Sparkles className="h-8 w-8" />
              </div>
              <h2 className="text-lg font-bold text-white">Ask Natural-Language Questions</h2>
              <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                TraceRAG retrieves matching vector passages and synthesizes an answer strictly grounded in your documents with page citations.
              </p>
              <div className="mt-6 w-full space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 text-left">
                  Try asking:
                </p>
                {[
                  "What is the primary purpose of Retrieval-Augmented Generation (RAG)?",
                  "Which cryptographic algorithms are mandatory for data at rest?",
                  "What is the required initial response time for Severity-1 incidents?",
                  "What is the secret recipe for dark chocolate soufflé?" // Will demonstrate refusal!
                ].map((sampleQ, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInputQuery(sampleQ);
                    }}
                    className="w-full text-left p-2.5 rounded-xl border border-navy-700/60 bg-navy-900/60 text-xs text-slate-300 hover:bg-navy-850 hover:border-indigo-500/40 transition flex items-center justify-between"
                  >
                    <span>{sampleQ}</span>
                    <ChevronRight className="h-3 w-3 text-slate-500 flex-shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === 'user';
              const isRefusal = msg.content.includes("do not contain sufficient information") || 
                                msg.content.includes("cannot be established from the available sources");

              return (
                <div
                  key={msg.id}
                  className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  {!isUser && (
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-600 text-white shadow-md shadow-indigo-600/30">
                      <Bot className="h-4 w-4" />
                    </div>
                  )}

                  <div className={`max-w-2xl rounded-2xl p-4 text-sm leading-relaxed ${
                    isUser
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20 rounded-tr-none'
                      : isRefusal
                      ? 'bg-navy-900 border border-amber-500/30 text-slate-200 rounded-tl-none shadow-sm'
                      : 'bg-navy-900 border border-navy-700 text-slate-200 rounded-tl-none shadow-sm'
                  }`}>
                    {/* Refusal Banner if evidence is missing */}
                    {!isUser && isRefusal && (
                      <div className="flex items-center gap-2 mb-2 pb-2 border-b border-amber-500/20 text-amber-400 text-xs font-semibold">
                        <ShieldAlert className="h-4 w-4 flex-shrink-0" />
                        <span>Evidence Absent — Refusal Triggered (No Hallucination)</span>
                      </div>
                    )}

                    {/* Grounded Banner if citations are present */}
                    {!isUser && !isRefusal && msg.citations && msg.citations.length > 0 && (
                      <div className="flex items-center justify-between mb-2 pb-2 border-b border-navy-700/60 text-xs text-emerald-400 font-medium">
                        <span className="flex items-center gap-1.5">
                          <ShieldCheck className="h-3.5 w-3.5" />
                          Evidence-Grounded Response
                        </span>
                        {msg.retrieved_chunks && msg.retrieved_chunks.length > 0 && (
                          <button
                            onClick={() => {
                              setInspectChunks(msg.retrieved_chunks);
                              setShowChunkDrawer(true);
                            }}
                            className="text-[11px] text-indigo-400 hover:text-indigo-300 underline"
                          >
                            Inspect {msg.retrieved_chunks.length} Context Chunks
                          </button>
                        )}
                      </div>
                    )}

                    {/* Content */}
                    <div className="whitespace-pre-wrap">{msg.content}</div>

                    {/* Source Citations */}
                    {!isUser && msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-navy-700/50">
                        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                          Verified Citations ({msg.citations.length}):
                        </div>
                        <div className="flex flex-wrap">
                          {msg.citations.map((c, idx) => (
                            <CitationBadge key={idx} citation={c} index={idx} />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {isUser && (
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-navy-800 text-slate-300 border border-navy-700">
                      <User className="h-4 w-4" />
                    </div>
                  )}
                </div>
              );
            })
          )}

          {loading && (
            <div className="flex gap-4 justify-start">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white animate-pulse">
                <Bot className="h-4 w-4" />
              </div>
              <div className="rounded-2xl rounded-tl-none border border-navy-700 bg-navy-900 p-4 text-xs text-slate-400 flex items-center gap-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 rounded-full bg-indigo-500 animate-bounce"></span>
                  <span className="h-2 w-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.2s]"></span>
                  <span className="h-2 w-2 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.4s]"></span>
                </div>
                <span>Executing vector retrieval & grounded synthesis...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <div className="border-t border-navy-700/60 bg-navy-900/80 p-4">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto flex gap-2">
            <input
              type="text"
              placeholder="Ask a question grounded in your documents..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={loading}
              className="flex-1 rounded-xl border border-navy-700 bg-navy-950 px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none transition disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !inputQuery.trim()}
              className="rounded-xl bg-indigo-600 px-5 py-3 text-white font-medium shadow-lg shadow-indigo-600/30 hover:bg-indigo-500 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send className="h-4 w-4" />
              <span>Ask</span>
            </button>
          </form>
          <div className="max-w-4xl mx-auto flex items-center justify-between text-[11px] text-slate-500 mt-2 px-1">
            <span>TraceRAG strictly refuses hallucinations if evidence is missing.</span>
            <span>Cosine similarity search via pgvector</span>
          </div>
        </div>
      </main>

      {/* Context Chunks Inspector Side Drawer */}
      {showChunkDrawer && (
        <aside className="w-96 flex-shrink-0 border-l border-navy-700/60 bg-navy-900/95 flex flex-col z-20 shadow-2xl">
          <div className="flex items-center justify-between p-4 border-b border-navy-700/60">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-indigo-400" />
              <h3 className="text-xs font-semibold text-white">Retrieved Context Passages</h3>
            </div>
            <button
              onClick={() => setShowChunkDrawer(false)}
              className="text-xs text-slate-400 hover:text-white"
            >
              Close
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {inspectChunks.map((chunk, idx) => (
              <div key={idx} className="p-3 rounded-xl border border-navy-700/70 bg-navy-850/80 space-y-2">
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span className="font-semibold text-indigo-300 truncate max-w-[150px]">
                    {chunk.document_name}
                  </span>
                  <span className="rounded bg-navy-700 px-1.5 py-0.5">Page {chunk.page_number}</span>
                  <span className="font-mono text-emerald-400">
                    {(chunk.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-normal whitespace-pre-wrap">
                  {chunk.text}
                </p>
              </div>
            ))}
          </div>
        </aside>
      )}
    </div>
  );
};

