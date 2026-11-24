import React from 'react';
import { 
  LayoutDashboard, 
  FolderKanban, 
  Sparkles, 
  Search, 
  BarChart3, 
  ShieldCheck,
  FileText
} from 'lucide-react';

export type PageId = 'dashboard' | 'knowledge' | 'workspace' | 'search' | 'evaluation';

interface NavbarProps {
  activePage: PageId;
  setActivePage: (page: PageId) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activePage, setActivePage }) => {
  const navItems = [
    { id: 'dashboard' as PageId, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'knowledge' as PageId, label: 'Knowledge Base', icon: FolderKanban },
    { id: 'workspace' as PageId, label: 'AI Workspace', icon: Sparkles },
    { id: 'search' as PageId, label: 'Search Explorer', icon: Search },
    { id: 'evaluation' as PageId, label: 'Evaluation Lab', icon: BarChart3 }
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-navy-700/60 bg-navy-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-indigo-400 text-white shadow-lg shadow-indigo-500/20">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-white">TraceRAG</span>
              <span className="rounded bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/20">
                PROD
              </span>
            </div>
            <p className="text-xs text-slate-400">Evidence-Grounded AI Knowledge Engine</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/25'
                    : 'text-slate-400 hover:bg-navy-800 hover:text-slate-200'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* System Status Indicator */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-navy-700 bg-navy-900/90 px-3 py-1 text-xs">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
            </span>
            <span className="text-slate-300 font-medium">pgvector Ready</span>
          </div>
        </div>
      </div>
    </header>
  );
};
