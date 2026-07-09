import { env } from '$env/dynamic/public';
import type { ComponentDetail, DashboardPayload, DemoDataset, ScenePayload } from './types';

const configuredBase = env.PUBLIC_API_BASE_URL?.replace(/\/$/, '');

function apiBase(): string {
  if (configuredBase) return configuredBase;
  if (typeof window !== 'undefined' && window.location.hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8000';
  }
  return '';
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...init?.headers
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export function getDashboard(): Promise<DashboardPayload> {
  return request<DashboardPayload>('/api/dashboard');
}

export function getRegionScene(regionId: number): Promise<ScenePayload> {
  return request<ScenePayload>(`/api/regions/${regionId}/scene`);
}

export function getComponentDetail(type: string, id: number): Promise<ComponentDetail> {
  return request<ComponentDetail>(`/api/components/${type}/${id}`);
}

export function resetDataset(): Promise<DemoDataset> {
  return request<DemoDataset>('/api/demo-datasets/reset', { method: 'POST' });
}

export function importTemplateDataset(): Promise<DemoDataset> {
  return request<DemoDataset>('/api/demo-datasets/import-template', { method: 'POST' });
}

export function getDatasetTemplate(): Promise<unknown> {
  return request<unknown>('/api/demo-datasets/template');
}

export function uploadDataset(data: unknown): Promise<DemoDataset> {
  return request<DemoDataset>('/api/demo-datasets/upload', {
    method: 'POST',
    body: JSON.stringify({ data })
  });
}
