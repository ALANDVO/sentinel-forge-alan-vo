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
// --- Usage Pattern types ---

export interface UsagePatternRequest {
  subscription_tier: 'free' | 'pro' | 'max';
  tokens_consumed: number;
  requests_made: number;
  duration_seconds: number;
  timestamp?: string; // ISO 8601
}

export interface UsagePatternResponse {
  id: string;
  subscription_tier: string;
  tokens_consumed: number;
  requests_made: number;
  duration_seconds: number;
  timestamp: string;
  created_at: string;
}

export interface UsagePatternListResponse {
  items: UsagePatternResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface UsageTrendResponse {
  period_start: string;
  period_end: string;
  total_tokens: number;
  total_requests: number;
  avg_tokens_per_request: number;
  token_rate_of_change: number;
  request_rate_of_change: number;
}

export interface UsagePredictionResponse {
  subscription_tier: string;
  current_period_tokens: number;
  current_period_requests: number;
  tokens_limit: number;
  requests_limit: number;
  tokens_used_pct: number;
  requests_used_pct: number;
  estimated_tokens_exhaustion: string | null;
  estimated_requests_exhaustion: string | null;
  days_until_tokens_exhaustion: number | null;
  days_until_requests_exhaustion: number | null;
  tokens_trend: 'increasing' | 'decreasing' | 'stable';
  requests_trend: 'increasing' | 'decreasing' | 'stable';
}

export interface AlertThresholdRequest {
  subscription_tier: 'free' | 'pro' | 'max';
  tokens_warning_threshold: number;
  tokens_critical_threshold: number;
  requests_warning_threshold: number;
  requests_critical_threshold: number;
}

export interface AlertThresholdResponse {
  id: string;
  subscription_tier: string;
  tokens_warning_threshold: number;
  tokens_critical_threshold: number;
  requests_warning_threshold: number;
  requests_critical_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface AlertCheckResponse {
  subscription_tier: string;
  current_tokens: number;
  current_requests: number;
  tokens_status: 'ok' | 'warning' | 'critical';
  requests_status: 'ok' | 'warning' | 'critical';
  tokens_warning_threshold: number;
  tokens_critical_threshold: number;
  requests_warning_threshold: number;
  requests_critical_threshold: number;
  tokens_warning_triggered: boolean;
  tokens_critical_triggered: boolean;
  requests_warning_triggered: boolean;
  requests_critical_triggered: boolean;
}

export type AnalysisStatus = 'idle' | 'loading' | 'success' | 'error';