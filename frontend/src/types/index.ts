/**
 * TypeScript types derived from the Sentinel Forge backend API schemas.
 *
 * These mirror the Pydantic models in backend/app/models/schemas.py.
 */

export type Severity = 'critical' | 'warning' | 'info';

export interface AnalyzeRequest {
  code: string;
  language?: 'typescript' | 'javascript';
  mod_name?: string | null;
}

export interface Finding {
  rule_id: string;
  rule_name: string;
  severity: string;
  line: number;
  column: number;
  message: string;
  suggestion: string;
  code_snippet: string;
}

export interface Summary {
  total: number;
  critical: number;
  warning: number;
  info: number;
}

export interface AnalysisResponse {
  analysis_id: string;
  code: string;
  language: string;
  mod_name: string | null;
  findings: Finding[];
  summary: Summary;
  created_at: string;
  duration_ms: number;
}

export interface RuleInfo {
  id: string;
  name: string;
  severity: string;
  description: string;
  message: string;
  suggestion: string;
  pattern: string;
}

export interface AnalysisRecord {
  id: string;
  mod_name: string | null;
  language: string;
  pages: number;
  total_findings: number;
  critical: number;
  warning: number;
  info: number;
  created_at: string;
  duration_ms: number;
}

export interface AnalysisListResponse {
  items: AnalysisRecord[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface SavedAnalysis {
  id: string;
  mod_name: string | null;
  language: string;
  code: string;
  findings: Finding[];
  summary: Summary;
  created_at: string;
  duration_ms: number;
}

export interface SaveAnalysisRequest {
  analysis_id: string;
  code: string;
  language: string;
  mod_name: string | null;
  findings: Finding[];
  summary: Summary;
  duration_ms: number;
}

export interface AuthVerifyResponse {
  authenticated: boolean;
  user: string | null;
  role: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface ListParams {
  page?: number;
  per_page?: number;
  severity?: string;
  mod_name?: string;
}

export type AnalysisStatus = 'idle' | 'loading' | 'success' | 'error';