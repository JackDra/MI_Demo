import { describe, expect, it } from 'vitest';
import { notificationSeverityForRegion } from './display';
import type { Notification, Region } from './types';

const region: Region = {
  id: 1,
  dataset_id: 1,
  slug: 'demo',
  name: 'Demo',
  summary: 'Demo',
  map_x: 0.5,
  map_y: 0.5,
  gps_lat: null,
  gps_lng: null,
  display: {}
};

function notification(severity: Notification['severity']): Notification {
  return {
    id: Math.random(),
    dataset_id: 1,
    region_id: 1,
    title: severity,
    contents: severity,
    severity,
    status: 'active',
    generated_from: 'test',
    source_entity_type: 'test',
    source_entity_id: null,
    map_x: 0.5,
    map_y: 0.5,
    prediction_horizon: null,
    prediction_method: null,
    predicted_for: null,
    created_at: new Date().toISOString()
  };
}

describe('notificationSeverityForRegion', () => {
  it('returns highest region severity', () => {
    expect(notificationSeverityForRegion(region, [notification('green'), notification('red')])).toBe(
      'red'
    );
  });

  it('defaults to green', () => {
    expect(notificationSeverityForRegion(region, [])).toBe('green');
  });
});
