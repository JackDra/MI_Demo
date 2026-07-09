import { getDashboard } from '$lib/api';

export async function load({ fetch }) {
  return {
    dashboard: await getDashboard(fetch)
  };
}
