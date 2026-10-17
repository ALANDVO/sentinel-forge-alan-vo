import { describe, it, expect, vi, beforeEach } from 'vitest';
import { SentinelForgeClient, ApiError } from '../src/api/client';

describe('SentinelForgeClient', () => {
  let client: SentinelForgeClient;

  beforeEach(() => {
    client = new SentinelForgeClient('http://localhost:9999');
  });

  it('analyzes code via POST /api/v1/analyze', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () =>
        Promise.resolve({
          analysis_id: 'abc',
          code: 'x',
          language: 'typescript',
          mod_name: null,
          findings: [],
          summary: { total: 0, critical: 0, warning: 0, info: 0 },
          created_at: '2024-01-01T00:00:00Z',
          duration_ms: 1.0,
        }),
    });
    global.fetch = mockFetch;

    const result = await client.analyze({ code: 'const x = 1;' });

    expect(result.analysis_id).toBe('abc');
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:9999/api/v1/analyze',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ code: 'const x = 1;', language: undefined, mod_name: undefined }),
      }),
    );
  });

  it('throws ApiError on 401 response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: () => Promise.resolve({ detail: 'Authentication required.' }),
    });

    await expect(client.listAnalyses()).rejects.toThrow(ApiError);
  });

  it('fetches rules via GET /api/v1/rules', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    });

    await client.listRules();

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:9999/api/v1/rules',
      expect.any(Object),
    );
  });

  it('includes API key header when set', async () => {
    client.setApiKey('secret-key');
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ authenticated: true, user: 'test', role: 'admin' }),
    });

    await client.verifyAuth();

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:9999/auth/verify',
      expect.objectContaining({
        headers: expect.objectContaining({ 'X-API-Key': 'secret-key' }),
      }),
    );
  });

  it('builds query string for listAnalyses', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          items: [],
          total: 0,
          page: 2,
          per_page: 10,
          pages: 0,
        }),
    });

    await client.listAnalyses({ page: 2, per_page: 10, severity: 'critical' });

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:9999/api/v1/analyses?page=2&per_page=10&severity=critical',
      expect.any(Object),
    );
  });
});