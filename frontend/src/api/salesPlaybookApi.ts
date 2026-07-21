import type {
  ProductDefinition,
  ProductSummary,
  SalesPlaybookDraft,
  SalesPlaybookVersion,
  SemanticBuyingRole,
} from '../types';

const baseUrl = 'http://127.0.0.1:8001/api/products';

export class SalesPlaybookApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'SalesPlaybookApiError';
  }
}

async function request<T>(path = '', init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
    const detail = typeof payload?.detail === 'string' ? payload.detail : `Request failed with ${response.status}`;
    throw new SalesPlaybookApiError(detail, response.status);
  }
  return response.json() as Promise<T>;
}

export const salesPlaybookApi = {
  listProducts: () => request<ProductSummary[]>(),
  createProduct: (product_code: string, name: string) => request<ProductSummary>('', {
    method: 'POST', body: JSON.stringify({ product_code, name, requester: 'ui' }),
  }),
  getDraft: (productId: string) => request<SalesPlaybookDraft>(`/${productId}/draft`),
  saveDraft: (
    productId: string,
    expected_revision: number,
    product: ProductDefinition,
    buying_roles: SemanticBuyingRole[],
  ) => request<SalesPlaybookDraft>(`/${productId}/draft`, {
    method: 'PUT',
    body: JSON.stringify({ expected_revision, updated_by: 'ui', product, buying_roles }),
  }),
  publish: (productId: string) => request<SalesPlaybookVersion>(`/${productId}/publish`, {
    method: 'POST', body: JSON.stringify({ requester: 'ui', activate: true }),
  }),
  listVersions: (productId: string) => request<SalesPlaybookVersion[]>(`/${productId}/versions`),
  activate: (productId: string, versionId: string) => request<SalesPlaybookVersion>(
    `/${productId}/versions/${versionId}/activate`, { method: 'POST' },
  ),
  restore: (productId: string, versionId: string) => request<SalesPlaybookDraft>(
    `/${productId}/versions/${versionId}/restore-as-draft`, {
      method: 'POST', body: JSON.stringify({ requester: 'ui' }),
    },
  ),
  archive: (productId: string) => request<ProductSummary>(`/${productId}/archive`, { method: 'POST' }),
};
