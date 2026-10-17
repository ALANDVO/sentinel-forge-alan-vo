import React, { useState, useEffect, useMemo } from 'react';
import { SentinelForgeClient, ApiError } from '../api/client';
import FindingsList from '../components/FindingsList';
import type { AnalysisRecord, SavedAnalysis, Summary } from '../types';

const client = new SentinelForgeClient();

const SEVERITY_FILTERS = [
  { value: '', label: 'All' },
  { value: 'critical', label: 'Critical' },
  { value: 'warning', label: 'Warning' },
  { value: 'info', label: 'Info' },
] as const;

export default function SavedAnalyses() {
  const [records, setRecords] = useState<AnalysisRecord[]>([]);
  const [selected, setSelected] = useState<SavedAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const perPage = 20;

  const load = async (pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await client.listAnalyses({
        page: pageNum,
        per_page: perPage,
        severity: severityFilter || undefined,
        mod_name: searchTerm || undefined,
      });
      setRecords(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const search = () => {
    setPage(1);
    load(1);
  };

  const clearSelection = () => {
    setSelected(null);
  };

  const handleExport = () => {
    if (!selected) return;
    const blob = new Blob([JSON.stringify(selected, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `saved-analysis-${selected.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (selected) {
    const summary: Summary = {
      total: selected.summary.total,
      critical: selected.summary.critical,
      warning: selected.summary.warning,
      info: selected.summary.info,
    };
    return (
      <div>
        <button className="btn-secondary" onClick={clearSelection}>
          ← Back to List
        </button>
        <div className="button-group">
          <button className="btn-secondary" onClick={handleExport}>
            Export JSON
          </button>
        </div>
        <div className="analysis-detail">
          <h2>{selected.mod_name || 'Unnamed Analysis'}</h2>
          <p className="text-muted">Language: {selected.language} · Saved: {new Date(selected.created_at).toLocaleString()}</p>
        </div>
        <FindingsList findings={selected.findings} summary={summary} />
      </div>
    );
  }

  return (
    <div>
      <div className="search-bar">
        <input
          type="text"
          className="search-input"
          placeholder="Search by mod name…"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          className="search-input"
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
        >
          {SEVERITY_FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
        <button className="btn" onClick={search} disabled={loading}>
          Search
        </button>
      </div>

      {loading && (
        <div className="status-state">
          <h3>Loading…</h3>
        </div>
      )}

      {!loading && error && (
        <div className="status-state">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {!loading && !error && records.length === 0 && (
        <div className="status-state">
          <h3>No Saved Analyses</h3>
          <p>No analyses have been saved yet.</p>
        </div>
      )}

      {!loading && !error && records.length > 0 && (
        <>
          <div className="analysis-list">
            {records.map((r) => (
              <div
                key={r.id}
                className="analysis-record"
                onClick={async () => {
                  try {
                    const detail = await client.getAnalysis(r.id);
                    setSelected(detail);
                  } catch (err) {
                    setError(err instanceof ApiError ? err.message : 'Failed to load');
                  }
                }}
              >
                <div>
                  <strong>{r.mod_name || 'Unnamed'}</strong>
                  <span className="text-muted"> — {r.language}</span>
                </div>
                <div className="text-muted">
                  {r.total_findings} findings • {new Date(r.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>

          <div className="pagination">
            <button
              className="btn-secondary"
              disabled={page === 1}
              onClick={() => { setPage((p) => Math.max(1, p - 1)); load(Math.max(1, page - 1)); }}
            >
              ← Prev
            </button>
            <span className="text-muted">
              Page {page} of {Math.ceil(total / perPage)}
            </span>
            <button
              className="btn-secondary"
              disabled={page >= Math.ceil(total / perPage)}
              onClick={() => { setPage((p) => p + 1); load(page + 1); }}
            >
              Next →
            </button>
          </div>
        </>
      )}
    </div>
  );
}