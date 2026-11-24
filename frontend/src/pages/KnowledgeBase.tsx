import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import { Document, DocumentDetail } from '../types';
import { ChunkInspectorModal } from '../components/ChunkInspectorModal';
import { 
  Upload, 
  FileText, 
  Trash2, 
  Eye, 
  Layers, 
  AlertCircle, 
  CheckCircle2, 
  Clock, 
  Sliders, 
  RefreshCw,
  FolderPlus
} from 'lucide-react';

export const KnowledgeBase: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedDocDetail, setSelectedDocDetail] = useState<DocumentDetail | null>(null);
  const [inspectLoading, setInspectLoading] = useState(false);

  // Ingestion config state
  const [chunkSize, setChunkSize] = useState<number>(500);
  const [chunkOverlap, setChunkOverlap] = useState<number>(100);
  const [showConfig, setShowConfig] = useState<boolean>(false);

  // Notifications
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Failed to load documents' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setNotification({ type: 'error', message: 'Only PDF documents are supported.' });
      return;
    }

    try {
      setUploading(true);
      setNotification(null);
      const doc = await api.uploadDocument(file, chunkSize, chunkOverlap);
      setNotification({
        type: 'success',
        message: `Successfully ingested "${doc.filename}" (${doc.total_chunks} chunks indexed).`
      });
      await loadDocuments();
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err.message || 'Failed to upload and process PDF.'
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}" and all its vector chunks?`)) {
      return;
    }

    try {
      await api.deleteDocument(docId);
      setNotification({
        type: 'success',
        message: `Deleted "${filename}" and purged vector embeddings.`
      });
      setDocuments(documents.filter(d => d.id !== docId));
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err.message || 'Failed to delete document.'
      });
    }
  };

  const handleInspect = async (docId: string) => {
    try {
      setInspectLoading(true);
      const detail = await api.getDocument(docId);
      setSelectedDocDetail(detail);
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err.message || 'Failed to load document chunks.'
      });
    } finally {
      setInspectLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Document Knowledge Base
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            Upload PDFs, configure sliding-window chunking, generate embeddings, and index into pgvector.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowConfig(!showConfig)}
            className={`flex items-center gap-2 rounded-lg border px-3.5 py-2 text-xs font-medium transition ${
              showConfig 
                ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300' 
                : 'border-navy-700 bg-navy-850 text-slate-300 hover:bg-navy-800'
            }`}
          >
            <Sliders className="h-3.5 w-3.5" />
            Ingestion Parameters
          </button>
          <button
            onClick={loadDocuments}
            className="flex items-center gap-2 rounded-lg border border-navy-700 bg-navy-850 px-3.5 py-2 text-xs font-medium text-slate-300 hover:bg-navy-800 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Notification Toast */}
      {notification && (
        <div className={`flex items-center justify-between rounded-xl p-4 border text-sm ${
          notification.type === 'success' 
            ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' 
            : 'border-rose-500/30 bg-rose-500/10 text-rose-300'
        }`}>
          <div className="flex items-center gap-2">
            {notification.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 text-rose-400 flex-shrink-0" />
            )}
            <span>{notification.message}</span>
          </div>
          <button onClick={() => setNotification(null)} className="text-xs font-bold ml-4">
            Dismiss
          </button>
        </div>
      )}

      {/* Ingestion Parameters Drawer */}
      {showConfig && (
        <div className="rounded-2xl border border-navy-700 bg-navy-900/90 p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-navy-700/60">
            <div>
              <h3 className="text-sm font-semibold text-white">Sliding-Window Chunking Parameters</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Applied to all subsequent PDF uploads. Overlap prevents semantic rupture across sentences.
              </p>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div>
              <div className="flex justify-between text-xs font-medium mb-1.5">
                <span className="text-slate-300">Chunk Size (characters)</span>
                <span className="text-indigo-400 font-mono">{chunkSize} chars</span>
              </div>
              <input
                type="range"
                min="100"
                max="2000"
                step="50"
                value={chunkSize}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setChunkSize(val);
                  if (chunkOverlap >= val) setChunkOverlap(Math.floor(val * 0.2));
                }}
                className="w-full accent-indigo-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">Recommended: 400 - 800 characters.</p>
            </div>

            <div>
              <div className="flex justify-between text-xs font-medium mb-1.5">
                <span className="text-slate-300">Chunk Overlap (characters)</span>
                <span className="text-indigo-400 font-mono">{chunkOverlap} chars</span>
              </div>
              <input
                type="range"
                min="0"
                max={Math.max(50, chunkSize - 50)}
                step="25"
                value={chunkOverlap}
                onChange={(e) => setChunkOverlap(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Preserves context across sentence boundaries ({Math.round((chunkOverlap / chunkSize) * 100)}% of chunk size).
              </p>
            </div>
          </div>
        </div>
      )}

      {/* PDF Upload Dropzone */}
      <div className="relative rounded-2xl border-2 border-dashed border-navy-700 hover:border-indigo-500/60 bg-navy-900/60 transition p-8 text-center group">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileUpload}
          disabled={uploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
        />
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:scale-105 transition">
            {uploading ? (
              <RefreshCw className="h-7 w-7 animate-spin text-indigo-400" />
            ) : (
              <Upload className="h-7 w-7 text-indigo-400" />
            )}
          </div>
          <div>
            <p className="text-sm font-semibold text-white">
              {uploading ? 'Extracting, chunking and embedding PDF...' : 'Click or drag PDF document to upload'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports standard multi-page PDFs. Text will be cleaned, chunked into {chunkSize}-char windows and embedded.
            </p>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <div className="rounded-2xl border border-navy-700 bg-navy-900/80 overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-navy-700/60 flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">Indexed Documents</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {documents.length} document{documents.length !== 1 ? 's' : ''} stored in knowledge repository
            </p>
          </div>
        </div>

        {documents.length === 0 ? (
          <div className="text-center py-16 px-4">
            <FileText className="h-12 w-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-slate-300">No Documents Uploaded</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Upload PDF files above or use the sample PDFs created in the project to populate your searchable knowledge base.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-navy-850/80 text-slate-400 font-medium uppercase tracking-wider border-b border-navy-700/60">
                <tr>
                  <th className="py-3 px-6">Document Name</th>
                  <th className="py-3 px-6">Status</th>
                  <th className="py-3 px-6">Size</th>
                  <th className="py-3 px-6">Pages</th>
                  <th className="py-3 px-6">Indexed Chunks</th>
                  <th className="py-3 px-6">Uploaded</th>
                  <th className="py-3 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-700/50 text-slate-300">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-navy-850/50 transition">
                    <td className="py-3.5 px-6 font-medium text-white flex items-center gap-2.5">
                      <FileText className="h-4 w-4 text-indigo-400 flex-shrink-0" />
                      <span className="truncate max-w-xs">{doc.filename}</span>
                    </td>
                    <td className="py-3.5 px-6">
                      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold border ${
                        doc.status === 'COMPLETED' 
                          ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                          : doc.status === 'PROCESSING'
                          ? 'border-indigo-500/30 bg-indigo-500/10 text-indigo-400'
                          : 'border-rose-500/30 bg-rose-500/10 text-rose-400'
                      }`}>
                        {doc.status === 'COMPLETED' && <CheckCircle2 className="h-3 w-3" />}
                        {doc.status === 'PROCESSING' && <Clock className="h-3 w-3 animate-spin" />}
                        {doc.status === 'FAILED' && <AlertCircle className="h-3 w-3" />}
                        {doc.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 text-slate-400 font-mono">
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td className="py-3.5 px-6 text-slate-300">
                      {doc.total_pages}
                    </td>
                    <td className="py-3.5 px-6 font-mono text-indigo-400 font-semibold">
                      {doc.total_chunks}
                    </td>
                    <td className="py-3.5 px-6 text-slate-400 text-[11px]">
                      {new Date(doc.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td className="py-3.5 px-6 text-right space-x-2">
                      <button
                        onClick={() => handleInspect(doc.id)}
                        className="inline-flex items-center gap-1 rounded-lg border border-navy-700 bg-navy-800 px-2.5 py-1 text-slate-300 hover:text-white hover:border-indigo-500 transition"
                        title="View Extracted Chunks"
                      >
                        <Eye className="h-3.5 w-3.5 text-indigo-400" />
                        <span>Chunks</span>
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="inline-flex items-center gap-1 rounded-lg border border-navy-700 bg-navy-800 px-2.5 py-1 text-slate-400 hover:text-rose-400 hover:border-rose-500/50 transition"
                        title="Delete Document"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Chunk Inspector Modal */}
      <ChunkInspectorModal
        document={selectedDocDetail}
        onClose={() => setSelectedDocDetail(null)}
      />
    </div>
  );
};
