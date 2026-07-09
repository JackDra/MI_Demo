import { error, redirect } from '@sveltejs/kit';
import { getComponentDetail, getDashboard, getRegionScene } from '$lib/api';
import { parsePlaceSlug, placePath } from '$lib/placeSlugs';

export async function load({ fetch, params }) {
  const dashboard = await getDashboard(fetch);
  const parsed = parsePlaceSlug(params.slug);

  if (!parsed) {
    error(404, 'Place not found');
  }

  const selectedLocation = dashboard.locations.find(
    (location) => location.type === parsed.type && location.id === parsed.id
  );

  if (!selectedLocation) {
    error(404, 'Place not found');
  }

  const canonicalPath = placePath(selectedLocation);
  if (`/places/${params.slug}` !== canonicalPath) {
    redirect(308, canonicalPath);
  }

  const [scene, componentDetail] = await Promise.all([
    getRegionScene(selectedLocation.region_id, fetch),
    getComponentDetail(selectedLocation.type, selectedLocation.id, fetch)
  ]);

  return {
    dashboard,
    scene,
    selectedLocation,
    componentDetail
  };
}
