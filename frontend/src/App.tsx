import React, { useState } from 'react';
import { Navbar, PageId } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { KnowledgeBase } from './pages/KnowledgeBase';
import { AIWorkspace } from './pages/AIWorkspace';
import { SearchExplorer } from './pages/SearchExplorer';
import { EvaluationLab } from './pages/EvaluationLab';

export const App: React.FC = () => {
  const [activePage, setActivePage] = useState<PageId>('dashboard');

  return (
    <div className="min-h-screen flex flex-col bg-navy-950 text-slate-100">
      {/* Navbar */}
      <Navbar activePage={activePage} setActivePage={setActivePage} />

      {/* Page Content */}
      <div className="flex-1">
        {activePage === 'dashboard' && <Dashboard setActivePage={setActivePage} />}
        {activePage === 'knowledge' && <KnowledgeBase />}
        {activePage === 'workspace' && <AIWorkspace />}
        {activePage === 'search' && <SearchExplorer />}
        {activePage === 'evaluation' && <EvaluationLab />}
      </div>
    </div>
  );
};

export default App;

