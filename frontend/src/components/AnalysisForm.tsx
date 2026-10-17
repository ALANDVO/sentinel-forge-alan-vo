import React, { useState } from 'react';
import type { AnalyzeRequest } from '../types';

interface AnalysisFormProps {
  onSubmit: (request: AnalyzeRequest) => void;
  loading?: boolean;
  disabled?: boolean;
}

const MAX_CODE_LENGTH = 100_000;

export default function AnalysisForm({ onSubmit, loading = false, disabled = false }: AnalysisFormProps) {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState<'typescript' | 'javascript'>('typescript');
  const [modName, setModName] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim() || code.length > MAX_CODE_LENGTH) return;
    onSubmit({ code, language, mod_name: modName || undefined });
  };

  const charPct = (code.length / MAX_CODE_LENGTH) * 100;
  const isOverLimit = code.length > MAX_CODE_LENGTH;

  return (
    <form className="analysis-form" onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label" htmlFor="mod-name">Mod Name (optional)</label>
        <input
          id="mod-name"
          type="text"
          className="search-input"
          placeholder="e.g. my-github-connector"
          value={modName}
          onChange={(e) => setModName(e.target.value)}
          maxLength={200}
        />
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="language">Language</label>
        <select
          id="language"
          className="search-input"
          value={language}
          onChange={(e) => setLanguage(e.target.value as 'typescript' | 'javascript')}
        >
          <option value="typescript">TypeScript</option>
          <option value="javascript">JavaScript</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label" htmlFor="code">Mod Source Code</label>
        <textarea
          id="code"
          className={`code-input ${isOverLimit ? 'error' : ''}`}
          placeholder="// Paste your Claude Code mod (function hook) source code here..."
          value={code}
          onChange={(e) => setCode(e.target.value)}
          rows={16}
          maxLength={MAX_CODE_LENGTH + 1000}
        />
        <div className="char-counter">
          <div className={`char-bar ${isOverLimit ? 'error' : ''}`} style={{ width: `${Math.min(charPct, 100)}%` }} />
          <span className={`char-count ${isOverLimit ? 'error' : ''}`}>
            {code.length.toLocaleString()} / {MAX_CODE_LENGTH.toLocaleString()}
          </span>
        </div>
      </div>

      <button type="submit" className="btn" disabled={loading || disabled || !code.trim() || isOverLimit}>
        {loading ? 'Analyzing…' : 'Analyze Mod'}
      </button>
    </form>
  );
}