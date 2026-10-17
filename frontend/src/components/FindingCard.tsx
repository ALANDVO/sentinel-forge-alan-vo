import type { Finding, Severity } from '../types';

interface FindingCardProps {
  finding: Finding;
}

const SEVERITY_LABELS: Record<Severity, string> = {
  critical: 'Critical',
  warning: 'Warning',
  info: 'Info',
};

export default function FindingCard({ finding }: FindingCardProps) {
  const severity = finding.severity as Severity;
  return (
    <div className={`finding-card ${severity}`}>
      <div className="finding-header">
        <span className={`severity-badge severity-${severity}`}>
          {SEVERITY_LABELS[severity]}
        </span>
        <span className="finding-rule">[{finding.rule_id}] {finding.rule_name}</span>
        <span className="finding-location">L{finding.line}:{finding.column}</span>
      </div>
      <div className="finding-message">{finding.message}</div>
      {finding.code_snippet && (
        <div className="code-snippet">{finding.code_snippet}</div>
      )}
      <div className="finding-suggestion">💡 {finding.suggestion}</div>
    </div>
  );
}