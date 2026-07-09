import { env } from '$env/dynamic/public';
import type {
  ComponentDetail,
  DashboardPayload,
  DemoDataset,
  ScenePayload
} from './types';

type Fetcher = typeof fetch;

export type MapAsset = {
  url: string;
  storage_bucket: string | null;
  storage_path: string | null;
  source: string;
};

const configuredBase = env.PUBLIC_API_BASE_URL?.replace(/\/$/, '');
const internalBase = process.env.INTERNAL_API_BASE_URL?.replace(/\/$/, '');

function apiBase(): string {
  if (typeof window === 'undefined') {
    return internalBase || configuredBase || 'http://127.0.0.1:8000';
  }
  if (configuredBase) return configuredBase;
  if (window.location.hostname === '127.0.0.1') {
    return 'http://127.0.0.1:8000';
  }
  return '';
}

async function request<T>(
  path: string,
  init?: RequestInit,
  fetcher: Fetcher = fetch
): Promise<T> {
  const response = await fetcher(`${apiBase()}${path}`, {
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

export function getDashboard(fetcher?: Fetcher): Promise<DashboardPayload> {
  return request<DashboardPayload>('/api/dashboard', undefined, fetcher);
}

export function getTopographicMapAsset(fetcher?: Fetcher): Promise<MapAsset> {
  return request<MapAsset>('/api/assets/topographic-map', undefined, fetcher);
}

export function getRegionScene(
  regionId: number,
  fetcher?: Fetcher
): Promise<ScenePayload> {
  return request<ScenePayload>(
    `/api/regions/${regionId}/scene`,
    undefined,
    fetcher
  );
}

export function getComponentDetail(
  type: string,
  id: number,
  fetcher?: Fetcher
): Promise<ComponentDetail> {
  return request<ComponentDetail>(
    `/api/components/${type}/${id}`,
    undefined,
    fetcher
  );
}

export function uploadDataset(data: unknown): Promise<DemoDataset> {
  return request<DemoDataset>('/api/demo-datasets/upload', {
    method: 'POST',
    body: JSON.stringify({ data })
  });
}
