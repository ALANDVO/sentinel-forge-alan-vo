import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import AnalysisForm from '../src/components/AnalysisForm';
import type { AnalyzeRequest } from '../src/types';

describe('AnalysisForm', () => {
  it('renders with a code textarea and submit button', () => {
    render(<AnalysisForm onSubmit={vi.fn()} />);

    expect(
      screen.getByPlaceholderText(/source code/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /analyze mod/i }),
    ).toBeInTheDocument();
  });

  it('renders language selector and mod name field', () => {
    render(<AnalysisForm onSubmit={vi.fn()} />);

    expect(screen.getByLabelText(/language/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/mod name/i)).toBeInTheDocument();
  });

  it('calls onSubmit with code when form is submitted', () => {
    const onSubmit = vi.fn();
    render(<AnalysisForm onSubmit={onSubmit} />);

    const textarea = screen.getByPlaceholderText(/source code/i);
    fireEvent.change(textarea, { target: { value: 'const x = 1;' } });

    const button = screen.getByRole('button', { name: /analyze mod/i });
    fireEvent.click(button);

    expect(onSubmit).toHaveBeenCalledTimes(1);
    const submitted: AnalyzeRequest = onSubmit.mock.calls[0][0];
    expect(submitted.code).toBe('const x = 1;');
    expect(submitted.language).toBe('typescript');
  });

  it('disables submit button when code is empty', () => {
    render(<AnalysisForm onSubmit={vi.fn()} />);

    const button = screen.getByRole('button', { name: /analyze mod/i });
    expect(button).toBeDisabled();
  });

  it('shows loading state when loading prop is true', () => {
    render(<AnalysisForm onSubmit={vi.fn()} loading={true} />);

    expect(
      screen.getByRole('button', { name: /analyzing/i }),
    ).toBeInTheDocument();
  });
});