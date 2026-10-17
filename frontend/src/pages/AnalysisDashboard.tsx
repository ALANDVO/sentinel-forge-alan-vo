import React, { useState } from 'react';
import { SentinelForgeClient, ApiError } from '../api/client';
import AnalysisForm from '../components/AnalysisForm';
import FindingsList from '../components/FindingsList';
import type { AnalysisResponse, AnalyzeRequest, AnalysisStatus } from '../types';

const client = new SentinelForgeClient();

export default function AnalysisDashboard() {
  const [status, setStatus] = useState<AnalysisStatus>('idle');
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (request: AnalyzeRequest) => {
    setStatus('loading');
    setError(null);
    setResult(null);
    try {
      const response = await client.analyze(request);
      setResult(response);
      setStatus('success');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'An unexpected error occurred');
      setStatus('error');
    }
  };

  const handleExport = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis-${result.analysis_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSave = async () => {
    if (!result) return;
    setStatus('loading');
    try {
      await client.saveAnalysis({
        analysis_id: result.analysis_id,
        code: result.code,
        language: result.language,
        mod_name: result.mod_name ?? null,
        findings: result.findings,
        summary: result.summary,
        duration_ms: result.duration_ms,
      });
      setStatus('success');
      alert('Analysis saved successfully.');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Save failed');
      setStatus('error');
    }
  };

  return (
    <div className="dashboard">
      <AnalysisForm
        onSubmit={handleAnalyze}
        loading={status === 'loading'}
        disabled={status === 'loading'}
      />

      {status === 'idle' && (
        <div className="status-state">
          <h3>Ready to Analyze</h3>
          <p>
            Paste your Claude Code mod (function hook) source code and click
            "Analyze Mod" to check for safety issues.
          </p>
        </div>
      )}

      {status === 'loading' && (
        <div className="status-state">
          <h3>Analyzing…</h3>
          <p>Running static analysis rules against your mod.</p>
        </div>
      )}

      {status === 'error' && (
        <div className="status-state">
          <h3>Analysis Failed</h3>
          <p>{error}</p>
        </div>
      )}

      {status === 'success' && result && (
        <div>
          <div className="button-group">
            <button className="btn" onClick={handleSave}>
              Save Analysis
            </button>
            <button className="btn-secondary" onClick={handleExport}>
              Export JSON
            </button>
          </div>
          <FindingsList findings={result.findings} summary={result.summary} />
        </div>
      )}
    </div>
  );
}