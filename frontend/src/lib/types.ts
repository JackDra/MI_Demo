export type Severity = 'green' | 'yellow' | 'red';

export interface DemoDataset {
  id: number;
  name: string;
  version: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  activated_at: string | null;
}

export interface Region {
  id: number;
  dataset_id: number;
  slug: string;
  name: string;
  summary: string;
  map_x: number;
  map_y: number;
  gps_lat: number | null;
  gps_lng: number | null;
  display: Record<string, unknown>;
}

export interface Notification {
  id: number;
  dataset_id: number;
  region_id: number | null;
  title: string;
  contents: string;
  severity: Severity;
  status: string;
  generated_from: string;
  source_entity_type: string;
  source_entity_id: number | null;
  map_x: number;
  map_y: number;
  prediction_horizon: string | null;
  prediction_method: string | null;
  predicted_for: string | null;
  created_at: string;
}

export interface DashboardPayload {
  dataset: DemoDataset | null;
  summary: {
    active_dataset_id: number | null;
    region_count: number;
    notification_count: number;
    red_count: number;
    yellow_count: number;
    green_count: number;
  };
  regions: Region[];
  notifications: Notification[];
}

export interface RiverSection {
  id: number;
  region_id: number;
  name: string;
  start_x: number;
  start_y: number;
  end_x: number;
  end_y: number;
  flow_rate_ml_per_day: number;
  target_flow_rate_ml_per_day: number;
  water_level_m: number;
  absorption_rate_percent: number;
  evaporation_rate_mm_per_day: number;
  display: Record<string, unknown>;
}

export interface Gate {
  id: number;
  region_id: number;
  name: string;
  asset_id: string;
  x: number;
  y: number;
  state: string;
  opening_percent: number;
  planned_action: string | null;
  planned_for: string | null;
  model: string | null;
  next_inspection_at: string | null;
}

export interface Sensor {
  id: number;
  region_id: number;
  name: string;
  sensor_id: string;
  sensor_type: string;
  x: number;
  y: number;
  reading: number;
  unit: string;
  health: string;
  last_updated_at: string;
  calibration_due_at: string | null;
  next_inspection_at: string | null;
}

export interface Reservoir {
  id: number;
  region_id: number;
  name: string;
  x: number;
  y: number;
  capacity_ml: number;
  current_amount_ml: number;
  percent_filled: number;
  low_threshold_percent: number;
}

export interface VegetationZone {
  id: number;
  region_id: number;
  name: string;
  x: number;
  y: number;
  risk_level: Severity;
  last_inspection_at: string | null;
  next_inspection_at: string | null;
  notes: string;
}

export interface ScenePayload {
  region: Region;
  notifications: Notification[];
  river_sections: RiverSection[];
  gates: Gate[];
  sensors: Sensor[];
  reservoirs: Reservoir[];
  vegetation_zones: VegetationZone[];
}

export interface ComponentDetail {
  component_type: string;
  component: Record<string, unknown>;
  notifications: Notification[];
  related_metrics: Record<string, unknown>;
}

export type SelectableComponent =
  | { type: 'river_section'; id: number; label: string }
  | { type: 'gate'; id: number; label: string }
  | { type: 'sensor'; id: number; label: string }
  | { type: 'reservoir'; id: number; label: string }
  | { type: 'vegetation_zone'; id: number; label: string };
