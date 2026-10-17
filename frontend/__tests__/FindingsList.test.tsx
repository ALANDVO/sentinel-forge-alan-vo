import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import FindingsList from '../src/components/FindingsList';
import type { Finding, Summary } from '../src/types';

const FINDINGS: Finding[] = [
  {
    rule_id: 'RL-001',
    rule_name: 'Unsafe Process Execution',
    severity: 'critical',
    line: 1,
    column: 7,
    message: 'Process execution detected.',
    suggestion: 'Register this side effect.',
    code_snippet: "const cp = require('child_process');",
  },
  {
    rule_id: 'RL-003',
    rule_name: 'Unsafe Network Call',
    severity: 'warning',
    line: 5,
    column: 3,
    message: 'Network call detected.',
    suggestion: 'Add timeout.',
    code_snippet: 'fetch(url);',
  },
  {
    rule_id: 'RL-004',
    rule_name: 'UI Flickering Pattern',
    severity: 'info',
    line: 10,
    column: 3,
    message: 'Full-screen redraw detected.',
    suggestion: 'Use line-specific updates.',
    code_snippet: 'console.clear();',
  },
];

const SUMMARY: Summary = { total: 3, critical: 1, warning: 1, info: 1 };

describe('FindingsList', () => {
  it('renders all findings with severity badges', () => {
    render(<FindingsList findings={FINDINGS} summary={SUMMARY} />);

    expect(screen.getAllByText('Critical').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Warning').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Info').length).toBeGreaterThan(0);
  });

  it('renders rule IDs and names for each finding', () => {
    render(<FindingsList findings={FINDINGS} summary={SUMMARY} />);

    expect(screen.getByText(/RL-001/)).toBeInTheDocument();
    expect(screen.getByText(/RL-003/)).toBeInTheDocument();
    expect(screen.getByText(/RL-004/)).toBeInTheDocument();
    expect(screen.getByText(/Unsafe Process Execution/)).toBeInTheDocument();
  });

  it('shows total count in summary header', () => {
    render(<FindingsList findings={FINDINGS} summary={SUMMARY} />);

    expect(screen.getByText('Total')).toBeInTheDocument();
  });

  it('filters findings by severity', () => {
    render(<FindingsList findings={FINDINGS} summary={SUMMARY} />);

    fireEvent.click(screen.getByRole('button', { name: 'Critical' }));

    expect(screen.queryByText(/RL-003/)).not.toBeInTheDocument();
    expect(screen.queryByText(/RL-004/)).not.toBeInTheDocument();
    expect(screen.getByText(/RL-001/)).toBeInTheDocument();
  });

  it('shows empty state when no findings', () => {
    render(
      <FindingsList findings={[]} summary={{ total: 0, critical: 0, warning: 0, info: 0 }} />,
    );

    expect(screen.getByText(/No Issues Found/)).toBeInTheDocument();
  });

  it('shows no-results message when filter matches nothing', () => {
    render(<FindingsList findings={FINDINGS} summary={SUMMARY} />);

    fireEvent.click(screen.getByRole('button', { name: 'Info' }));

    expect(screen.queryByText(/RL-001/)).not.toBeInTheDocument();
    expect(screen.queryByText(/RL-003/)).not.toBeInTheDocument();
    expect(screen.getByText(/RL-004/)).toBeInTheDocument();
  });
});