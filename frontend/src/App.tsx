import React, { useState } from 'react';
import AnalysisDashboard from './pages/AnalysisDashboard';
import SavedAnalyses from './pages/SavedAnalyses';
import './App.css';

type Page = 'analyze' | 'saved';

const TABS: { id: Page; label: string }[] = [
  { id: 'analyze', label: 'Analyze Mod' },
  { id: 'saved', label: 'Saved Analyses' },
];

export default function App() {
  const [page, setPage] = useState<Page>('analyze');

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="app-title">Sentinel Forge</h1>
        <nav className="app-nav">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`nav-button ${page === tab.id ? 'active' : ''}`}
              onClick={() => setPage(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>
      <main className="app-main">
        {page === 'analyze' ? <AnalysisDashboard /> : <SavedAnalyses />}
      </main>
    </div>
  );
}