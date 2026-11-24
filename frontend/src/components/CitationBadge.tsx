import React, { useState } from 'react';
import { Citation } from '../types';
import { FileText, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';

interface CitationBadgeProps {
  citation: Citation;
  index: number;
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ citation, index }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="inline-block mr-2 my-1">
      <div 
        className={`rounded-lg border transition-all text-xs cursor-pointer ${
          expanded 
            ? 'border-indigo-500/50 bg-navy-800 shadow-md shadow-indigo-500/10' 
            : 'border-navy-700 bg-navy-850/90 hover:border-indigo-500/40 text-slate-300'
        }`}
      >
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-200"
          type="button"
        >
          <FileText className="h-3 w-3 text-indigo-400" />
          <span className="text-indigo-300 font-semibold">[{index + 1}]</span>
          <span className="truncate max-w-[130px]">{citation.source_document}</span>
          <span className="rounded bg-navy-700 px-1 py-0.2 text-[10px] text-slate-300">
            P.{citation.page_number}
          </span>
          {expanded ? (
            <ChevronUp className="h-3 w-3 text-slate-400" />
          ) : (
            <ChevronDown className="h-3 w-3 text-slate-400" />
          )}
        </button>

        {expanded && (
          <div className="p-2.5 border-t border-navy-700/60 bg-navy-900/90 text-left rounded-b-lg space-y-1.5 max-w-sm">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="font-semibold text-indigo-300">Document Source Excerpt</span>
              <span className="font-mono text-emerald-400">
                Score: {(citation.similarity_score * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-slate-300 text-xs italic leading-relaxed border-l-2 border-indigo-500 pl-2">
              "{citation.excerpt}"
            </p>
            <div className="text-[10px] text-slate-500 font-mono">
              Chunk ID: {citation.chunk_id ? `${citation.chunk_id.slice(0, 8)}...` : 'N/A'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
