import type { DashboardLocation, LocationType } from './types';

const typeTokens: Record<LocationType, string> = {
  reservoir: 'reservoir',
  river_section: 'river'
};

const tokenTypes: Record<string, LocationType> = {
  reservoir: 'reservoir',
  river: 'river_section'
};

export type ParsedPlaceSlug = {
  type: LocationType;
  id: number;
};

export function slugifyPlaceName(value: string): string {
  return (
    value
      .toLowerCase()
      .replace(/&/g, ' and ')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'place'
  );
}

export function placeSlug(
  location: Pick<DashboardLocation, 'type' | 'id' | 'label'>
): string {
  return `${slugifyPlaceName(location.label)}-${typeTokens[location.type]}-${location.id}`;
}

export function placePath(
  location: Pick<DashboardLocation, 'type' | 'id' | 'label'>
): string {
  return `/places/${placeSlug(location)}`;
}

export function parsePlaceSlug(slug: string): ParsedPlaceSlug | null {
  const match = slug.match(/-(reservoir|river)-(\d+)$/);
  if (!match) return null;

  return {
    type: tokenTypes[match[1]],
    id: Number(match[2])
  };
}
