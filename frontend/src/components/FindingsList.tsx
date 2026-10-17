import React, { useState, useMemo } from 'react';
import type { Finding, Summary } from '../types';
import FindingCard from './FindingCard';

interface FindingsListProps {
  findings: Finding[];
  summary: Summary;
}

type Filter = 'all' | 'critical' | 'warning' | 'info';

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'critical', label: 'Critical' },
  { value: 'warning', label: 'Warnings' },
  { value: 'info', label: 'Info' },
];

export default function FindingsList({ findings, summary }: FindingsListProps) {
  const [filter, setFilter] = useState<Filter>('all');

  const filtered = useMemo(() => {
    if (filter === 'all') return findings;
    return findings.filter((f) => f.severity === filter);
  }, [findings, filter]);

  if (findings.length === 0) {
    return (
      <div className="status-state">
        <h3>No Issues Found</h3>
        <p>Your mod passed all safety checks.</p>
      </div>
    );
  }

  return (
    <div className="findings-list">
      <div className="summary-header">
        <div className="summary-chip">
          <div className="count">{summary.total}</div>
          <div className="label">Total</div>
        </div>
        <div className="summary-chip">
          <div className="count" style={{ color: '#ff4757' }}>{summary.critical}</div>
          <div className="label">Critical</div>
        </div>
        <div className="summary-chip">
          <div className="count" style={{ color: '#ff9f43' }}>{summary.warning}</div>
          <div className="label">Warnings</div>
        </div>
        <div className="summary-chip">
          <div className="count" style={{ color: '#00d2d3' }}>{summary.info}</div>
          <div className="label">Info</div>
        </div>
      </div>

      <div className="filter-bar">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            className={`filter-button ${filter === f.value ? 'active' : ''}`}
            onClick={() => setFilter(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="findings-container">
        {filtered.length === 0 ? (
          <p className="no-results">No findings match the selected filter.</p>
        ) : (
          filtered.map((f, i) => (
            <FindingCard key={`${f.rule_id}-${f.line}-${i}`} finding={f} />
          ))
        )}
      </div>
    </div>
  );
}