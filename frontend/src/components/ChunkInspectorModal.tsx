import React, { useState } from 'react';
import { DocumentDetail, DocumentChunk } from '../types';
import { X, FileText, Layers, Hash, Calendar, Search } from 'lucide-react';

interface ChunkInspectorModalProps {
  document: DocumentDetail | null;
  onClose: () => void;
}

export const ChunkInspectorModal: React.FC<ChunkInspectorModalProps> = ({ document, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');

  if (!document) return null;

  const filteredChunks = (document.chunks || []).filter(c => 
    c.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.chunk_index.toString().includes(searchTerm) ||
    c.page_number.toString().includes(searchTerm)
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative flex flex-col w-full max-w-4xl max-h-[85vh] rounded-2xl border border-navy-700 bg-navy-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-navy-700/80 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">{document.filename}</h3>
              <div className="flex items-center gap-3 text-xs text-slate-400">
                <span>{document.total_pages} Pages</span>
                <span>•</span>
                <span>{document.total_chunks} Chunks Indexed</span>
                <span>•</span>
                <span>{(document.file_size / 1024).toFixed(1)} KB</span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-navy-800 hover:text-white transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center justify-between border-b border-navy-700/50 px-6 py-3 bg-navy-850/50">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search in chunks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full rounded-lg border border-navy-700 bg-navy-900 py-1.5 pl-9 pr-4 text-xs text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Showing {filteredChunks.length} of {document.chunks?.length || 0} chunks
          </span>
        </div>

        {/* Chunks List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {filteredChunks.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              No chunks matched your filter criteria.
            </div>
          ) : (
            filteredChunks.map((chunk) => (
              <div
                key={chunk.id}
                className="rounded-xl border border-navy-700/80 bg-navy-850/80 p-4 transition hover:border-indigo-500/40"
              >
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-navy-700/50 text-xs text-slate-400 font-mono">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-indigo-500/10 px-2 py-0.5 text-indigo-400 font-semibold border border-indigo-500/20">
                      Chunk #{chunk.chunk_index}
                    </span>
                    <span className="rounded bg-navy-700 px-2 py-0.5 text-slate-300">
                      Page {chunk.page_number}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span>{chunk.token_count} tokens</span>
                    <span className="text-slate-500">ID: {chunk.id.slice(0, 8)}...</span>
                  </div>
                </div>
                <p className="text-sm text-slate-200 leading-relaxed font-normal whitespace-pre-wrap">
                  {chunk.text}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

