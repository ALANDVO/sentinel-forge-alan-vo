/**
 * Typed API client for the Sentinel Forge backend.
 *
 * Derived from the actual route definitions in backend/app/api/analysis.py
 * and backend/app/api/auth.py. Uses the native fetch API.
 */
import type {
  AnalysisListResponse,
  AnalysisResponse,
  AnalyzeRequest,
  AuthVerifyResponse,
  HealthResponse,
  ListParams,
  RuleInfo,
  SaveAnalysisRequest,
  AnalysisRecord,
  SavedAnalysis,
} from '../types';

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(`API ${status}: ${message}`);
    this.name = 'ApiError';
  }
}

export class SentinelForgeClient {
  private baseUrl: string;
  private apiKey: string | null;

  constructor(
    baseUrl: string = (() => {
      if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) {
        return import.meta.env.VITE_API_URL;
      }
      return 'http://127.0.0.1:8000';
    })(),
    apiKey: string | null = null,
  ) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.apiKey = apiKey;
  }

  setApiKey(key: string | null): void {
    this.apiKey = key;
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(this.apiKey ? { 'X-API-Key': this.apiKey } : {}),
      ...(init.headers as Record<string, string> || {}),
    };

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers,
    });

    if (!response.ok) {
      let errorMessage = response.statusText;
      try {
        const body = await response.json();
        errorMessage = body.detail || body.message || response.statusText;
      } catch {
        // non-JSON error
      }
      throw new ApiError(response.status, errorMessage);
    }

    if (response.status === 204) {
      return null as unknown as T;
    }

    return response.json() as Promise<T>;
  }

  // --- Analysis endpoints ---

  async analyze(req: AnalyzeRequest): Promise<AnalysisResponse> {
    return this.request<AnalysisResponse>('/api/v1/analyze', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async listRules(): Promise<RuleInfo[]> {
    return this.request<RuleInfo[]>('/api/v1/rules');
  }

  async saveAnalysis(req: SaveAnalysisRequest): Promise<AnalysisRecord> {
    return this.request<AnalysisRecord>('/api/v1/analyses', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  async listAnalyses(params?: ListParams): Promise<AnalysisListResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.per_page) query.set('per_page', String(params.per_page));
    if (params?.severity) query.set('severity', params.severity);
    if (params?.mod_name) query.set('mod_name', params.mod_name);
    const qs = query.toString();
    return this.request<AnalysisListResponse>(
      `/api/v1/analyses${qs ? `?${qs}` : ''}`,
    );
  }

  async getAnalysis(id: string): Promise<SavedAnalysis> {
    return this.request<SavedAnalysis>(`/api/v1/analyses/${encodeURIComponent(id)}`);
  }

  // --- Auth endpoints ---

  async verifyAuth(): Promise<AuthVerifyResponse> {
    return this.request<AuthVerifyResponse>('/auth/verify');
  }

  async logout(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/auth/logout', {
      method: 'POST',
    });
  }

  // --- Health ---

  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }
}

export const defaultClient = new SentinelForgeClient();