<script lang="ts">
  import { tick } from 'svelte';
  import { Canvas, T } from '@threlte/core';
  import * as THREE from 'three';
  import FlowingRiverSurface from './FlowingRiverSurface.svelte';
  import OrbitRig from './OrbitRig.svelte';
  import type {
    Gate,
    Reservoir,
    RiverSection,
    ScenePayload,
    SelectableComponent,
    Sensor,
    VegetationZone
  } from '$lib/types';

  export let scene: ScenePayload;
  export let selectedComponentKey: string | null;
  export let focusLocationType: 'river_section' | 'reservoir' = 'river_section';
  export let focusLocationId: number | null = null;
  export let onSelectComponent: (component: SelectableComponent) => void;

  $: focusedReservoir = scene.reservoirs.find(
    (item) => item.id === focusLocationId
  );

  type TooltipRow = {
    label: string;
    value: string;
  };

  type TooltipState = {
    title: string;
    type: string;
    rows: TooltipRow[];
    anchorX: number;
    anchorY: number;
    x: number;
    y: number;
  };

  type HoverItem = RiverSection | Gate | Sensor | Reservoir | VegetationZone;

  type HoverTarget = {
    object: THREE.Object3D;
    type: SelectableComponent['type'];
    item: HoverItem;
  };

  type ReservoirGroundPanel = {
    x: number;
    z: number;
    width: number;
    depth: number;
    color: string;
  };

  let sceneShell: HTMLDivElement;
  let cameraRef: THREE.PerspectiveCamera;
  let tooltipElement: HTMLDivElement;
  let tooltip: TooltipState | null = null;
  let hoverTargets: HoverTarget[] = [];
  let tooltipPlacementId = 0;
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const tooltipMargin = 16;
  const tooltipOffset = 14;

  function key(type: string, id: number): string {
    return `${type}:${id}`;
  }

  function isSelected(type: string, id: number): boolean {
    return selectedComponentKey === key(type, id);
  }

  function select(
    type: SelectableComponent['type'],
    id: number,
    label: string
  ): void {
    onSelectComponent({ type, id, label } as SelectableComponent);
  }

  function px(value: number): number {
    return focusLocationType === 'reservoir' && focusedReservoir
      ? value - focusedReservoir.x
      : value;
  }

  function py(value: number): number {
    return focusLocationType === 'reservoir' && focusedReservoir
      ? value - focusedReservoir.y
      : value;
  }

  function reservoirRadius(reservoir: Reservoir): number {
    return focusLocationType === 'reservoir' && reservoir.id === focusLocationId
      ? 2.45
      : 0.72;
  }

  function reservoirWaterRadius(reservoir: Reservoir): number {
    return focusLocationType === 'reservoir' && reservoir.id === focusLocationId
      ? 2.58
      : 0.66;
  }

  function reservoirWaterSurfaceY(reservoir: Reservoir): number {
    return 0.48 + reservoirWaterHeight(reservoir) / 2 + 0.012;
  }

  function reservoirWaterHeight(reservoir: Reservoir): number {
    if (focusLocationType === 'reservoir' && reservoir.id === focusLocationId) {
      return 0.12 + (clampPercent(reservoir.percent_filled) / 100) * 0.62;
    }

    return (
      0.06 +
      Math.max(
        0.08,
        Math.min(0.22, (clampPercent(reservoir.percent_filled) / 100) * 0.22)
      )
    );
  }

  function focusedReservoirWaterSurfaceWorldY(): number {
    if (!focusedReservoir) return 0.22;
    return reservoirPosition(focusedReservoir)[1] + reservoirWaterSurfaceY(focusedReservoir);
  }

  function focusedReservoirWaterSideHeight(): number {
    return Math.max(0.2, focusedReservoirWaterSurfaceWorldY() + 1.03);
  }

  function focusedReservoirWaterSideY(): number {
    return (focusedReservoirWaterSurfaceWorldY() - 1.03) / 2;
  }

  function labelFor(value: string): string {
    return value.replaceAll('_', ' ');
  }

  function formatTooltipValue(value: unknown): string {
    if (value === null || value === undefined || value === '') return 'n/a';
    if (typeof value === 'number') {
      return Number.isInteger(value) ? String(value) : value.toFixed(2);
    }
    if (typeof value === 'boolean') return value ? 'yes' : 'no';
    if (Array.isArray(value)) return value.map(formatTooltipValue).join(', ');
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }

  function rowsFromObject(values: Record<string, unknown>): TooltipRow[] {
    return Object.entries(values).map(([label, value]) => ({
      label: labelFor(label),
      value: formatTooltipValue(value)
    }));
  }

  function metadataRows(
    metadata: Record<string, unknown> | undefined
  ): TooltipRow[] {
    if (!metadata || Object.keys(metadata).length === 0) return [];
    return rowsFromObject(metadata);
  }

  function channelLength(): number {
    return 72;
  }

  function channelRadius(): number {
    return 1.35;
  }

  function reservoirInletLength(): number {
    return 5.8;
  }

  function reservoirInletWidth(): number {
    return 1.05;
  }

  function reservoirInletX(): number {
    return -4.35;
  }

  function reservoirInletStartX(): number {
    return reservoirInletX() - reservoirInletLength() / 2 - 0.5;
  }

  function reservoirGatePosition(index: number): [number, number, number] {
    return [-2.72 - index * 0.28, 0.64, 0];
  }

  function reservoirSensorPosition(index: number): [number, number, number] {
    const column = Math.floor(index / 2);
    const side = index % 2 === 0 ? -1 : 1;
    return [3.55 + column * 0.32, 0.86, side * 1.28];
  }

  function reservoirVegetationPosition(index: number): [number, number, number] {
    const side = index % 2 === 0 ? 1 : -1;
    return [3.3 + Math.floor(index / 2) * 0.34, 0.26, side * 1.72];
  }

  function reservoirPosition(reservoir: Reservoir): [number, number, number] {
    if (focusLocationType === 'reservoir') {
      return [px(reservoir.x), -0.55, py(reservoir.y)];
    }

    const channelSide = reservoir.y >= 0 ? 1 : -1;
    return [px(reservoir.x), -0.02, channelSide * (channelRadius() + 2.15)];
  }

  function groundWidth(): number {
    return focusLocationType === 'reservoir' ? 46 : 92;
  }

  function groundDepth(): number {
    return focusLocationType === 'reservoir' ? 26 : 44;
  }

  function channelCutoutWidth(): number {
    return 3.2;
  }

  function bankDepth(): number {
    return (groundDepth() - channelCutoutWidth()) / 2;
  }

  function endCapWidth(): number {
    return (groundWidth() - channelLength()) / 2;
  }

  function reservoirGroundPanels(): ReservoirGroundPanel[] {
    const width = groundWidth();
    const depth = groundDepth();
    const halfWidth = width / 2;
    const halfDepth = depth / 2;
    const basinClearance = 3.42;
    const inletClearance = reservoirInletWidth() / 2 + 0.18;
    const inletLeftEdge =
      reservoirInletX() - reservoirInletLength() / 2 - 0.72;
    const leftPanelWidth = Math.max(0.1, inletLeftEdge + halfWidth);
    const leftPanelX = -halfWidth + leftPanelWidth / 2;
    const inletSideWidth = Math.max(0.1, -basinClearance - inletLeftEdge);
    const inletSideX = inletLeftEdge + inletSideWidth / 2;
    const sideBandDepth = basinClearance - inletClearance;

    return [
      {
        x: 0,
        z: basinClearance + (halfDepth - basinClearance) / 2,
        width,
        depth: halfDepth - basinClearance,
        color: '#40533a'
      },
      {
        x: 0,
        z: -basinClearance - (halfDepth - basinClearance) / 2,
        width,
        depth: halfDepth - basinClearance,
        color: '#374c35'
      },
      {
        x: basinClearance + (halfWidth - basinClearance) / 2,
        z: 0,
        width: halfWidth - basinClearance,
        depth: basinClearance * 2,
        color: '#3c5237'
      },
      {
        x: leftPanelX,
        z: inletClearance + sideBandDepth / 2,
        width: leftPanelWidth,
        depth: sideBandDepth,
        color: '#42573c'
      },
      {
        x: leftPanelX,
        z: -inletClearance - sideBandDepth / 2,
        width: leftPanelWidth,
        depth: sideBandDepth,
        color: '#354932'
      },
      {
        x: leftPanelX,
        z: 0,
        width: leftPanelWidth,
        depth: inletClearance * 2,
        color: '#384f36'
      },
      {
        x: inletSideX,
        z: inletClearance + sideBandDepth / 2,
        width: inletSideWidth,
        depth: sideBandDepth,
        color: '#3e5339'
      },
      {
        x: inletSideX,
        z: -inletClearance - sideBandDepth / 2,
        width: inletSideWidth,
        depth: sideBandDepth,
        color: '#344831'
      }
    ];
  }

  function sceneryPositions(side: -1 | 1): Array<[number, number, number]> {
    return [
      [-30, 0.1, side * 3.3],
      [-24, 0.1, side * 5.8],
      [-17, 0.1, side * 3.9],
      [-9.5, 0.1, side * 6.6],
      [-1.5, 0.1, side * 4.4],
      [7.5, 0.1, side * 6.1],
      [16, 0.1, side * 3.7],
      [24, 0.1, side * 6.8],
      [32, 0.1, side * 4.8]
    ];
  }

  function cloudPositions(): Array<[number, number, number, number]> {
    return [
      [-22, 7.2, -20, 1.45],
      [-6, 8.0, -23, 1.75],
      [12, 7.5, -21, 1.55],
      [25, 6.7, -16, 1.15]
    ];
  }

  function clampPercent(value: number): number {
    return Math.min(100, Math.max(0, value));
  }

  function displayNumber(
    display: Record<string, unknown>,
    key: string
  ): number | null {
    const value = display[key];
    return typeof value === 'number' && Number.isFinite(value) ? value : null;
  }

  function riverFillPercent(river: RiverSection): number {
    const displayFillPercent =
      displayNumber(river.display, 'percent_filled') ??
      displayNumber(river.display, 'fill_percent');

    if (
      typeof river.percent_filled === 'number' &&
      Number.isFinite(river.percent_filled)
    ) {
      return clampPercent(river.percent_filled);
    }

    if (displayFillPercent !== null) {
      return clampPercent(displayFillPercent);
    }

    const maxWaterLevel =
      displayNumber(river.display, 'max_water_level_m') ?? 2;
    if (maxWaterLevel <= 0) return 0;
    return clampPercent((river.water_level_m / maxWaterLevel) * 100);
  }

  function tooltipRowsFor(
    type: SelectableComponent['type'],
    item: HoverItem
  ): TooltipRow[] {
    if (type === 'river_section') {
      const river = item as RiverSection;
      return [
        ...rowsFromObject({
          flow_rate_ml_per_day: river.flow_rate_ml_per_day,
          target_flow_rate_ml_per_day: river.target_flow_rate_ml_per_day,
          water_level_m: river.water_level_m,
          percent_filled: riverFillPercent(river),
          absorption_rate_percent: river.absorption_rate_percent,
          evaporation_rate_mm_per_day: river.evaporation_rate_mm_per_day
        }),
        ...metadataRows(river.display)
      ];
    }

    if (type === 'gate') {
      const gate = item as Gate;
      return [
        ...rowsFromObject({
          asset_id: gate.asset_id,
          state: gate.state,
          opening_percent: gate.opening_percent,
          planned_action: gate.planned_action,
          planned_for: gate.planned_for,
          model: gate.model,
          next_inspection_at: gate.next_inspection_at
        }),
        ...metadataRows(gate.metadata_json)
      ];
    }

    if (type === 'sensor') {
      const sensor = item as Sensor;
      return [
        ...rowsFromObject({
          sensor_id: sensor.sensor_id,
          sensor_type: sensor.sensor_type,
          reading: `${formatTooltipValue(sensor.reading)} ${sensor.unit}`,
          health: sensor.health,
          last_updated_at: sensor.last_updated_at,
          calibration_due_at: sensor.calibration_due_at,
          next_inspection_at: sensor.next_inspection_at
        }),
        ...metadataRows(sensor.metadata_json)
      ];
    }

    if (type === 'reservoir') {
      const reservoir = item as Reservoir;
      return [
        ...rowsFromObject({
          capacity_ml: reservoir.capacity_ml,
          current_amount_ml: reservoir.current_amount_ml,
          percent_filled: reservoir.percent_filled,
          low_threshold_percent: reservoir.low_threshold_percent
        }),
        ...metadataRows(reservoir.metadata_json)
      ];
    }

    const vegetation = item as VegetationZone;
    return rowsFromObject({
      risk_level: vegetation.risk_level,
      last_inspection_at: vegetation.last_inspection_at,
      next_inspection_at: vegetation.next_inspection_at,
      notes: vegetation.notes
    });
  }

  function pointerPosition(
    event: MouseEvent | PointerEvent
  ): { x: number; y: number } | null {
    if (!sceneShell) return null;

    const bounds = sceneShell.getBoundingClientRect();
    return {
      x: event.clientX - bounds.left,
      y: event.clientY - bounds.top
    };
  }

  function clamp(value: number, min: number, max: number): number {
    return Math.max(min, Math.min(value, max));
  }

  function placeTooltip(
    position: { x: number; y: number },
    size: { width: number; height: number }
  ): { x: number; y: number } {
    const bounds = sceneShell.getBoundingClientRect();
    const maxX = Math.max(
      tooltipMargin,
      bounds.width - size.width - tooltipMargin
    );
    const maxY = Math.max(
      tooltipMargin,
      bounds.height - size.height - tooltipMargin
    );
    const preferredX = position.x + tooltipOffset;
    const preferredY = position.y + tooltipOffset;
    const flippedX = position.x - size.width - tooltipOffset;
    const flippedY = position.y - size.height - tooltipOffset;

    return {
      x: clamp(preferredX > maxX ? flippedX : preferredX, tooltipMargin, maxX),
      y: clamp(preferredY > maxY ? flippedY : preferredY, tooltipMargin, maxY)
    };
  }

  async function refineTooltipPlacement(placementId: number): Promise<void> {
    await tick();
    if (!tooltip || placementId !== tooltipPlacementId || !tooltipElement) {
      return;
    }

    const bounds = tooltipElement.getBoundingClientRect();
    const nextPosition = placeTooltip(
      { x: tooltip.anchorX, y: tooltip.anchorY },
      { width: bounds.width, height: bounds.height }
    );

    if (nextPosition.x !== tooltip.x || nextPosition.y !== tooltip.y) {
      tooltip = { ...tooltip, ...nextPosition };
    }
  }

  function showTooltipAt(
    position: { x: number; y: number },
    type: SelectableComponent['type'],
    item: HoverItem
  ): void {
    const bounds = sceneShell.getBoundingClientRect();
    const estimatedSize = {
      width: Math.min(320, Math.max(0, bounds.width - tooltipMargin * 2)),
      height: 220
    };
    const nextPosition = placeTooltip(position, estimatedSize);
    const placementId = ++tooltipPlacementId;

    tooltip = {
      title: item.name,
      type: labelFor(type),
      rows: tooltipRowsFor(type, item).filter((row) => row.value !== 'n/a'),
      anchorX: position.x,
      anchorY: position.y,
      x: nextPosition.x,
      y: nextPosition.y
    };

    void refineTooltipPlacement(placementId);
  }

  function hideTooltip(): void {
    tooltipPlacementId += 1;
    tooltip = null;
  }

  function registerHoverTarget(
    object: THREE.Object3D,
    type: SelectableComponent['type'],
    item: HoverItem
  ): () => void {
    const target = { object, type, item };
    hoverTargets = [...hoverTargets, target];
    return () => {
      hoverTargets = hoverTargets.filter((candidate) => candidate !== target);
    };
  }

  function handleScenePointerMove(event: PointerEvent): void {
    const position = pointerPosition(event);
    if (!position || !cameraRef || hoverTargets.length === 0) {
      hideTooltip();
      return;
    }

    const bounds = sceneShell.getBoundingClientRect();
    pointer.set(
      (position.x / bounds.width) * 2 - 1,
      -(position.y / bounds.height) * 2 + 1
    );
    cameraRef.updateMatrixWorld();
    raycaster.setFromCamera(pointer, cameraRef);

    const intersections = raycaster.intersectObjects(
      hoverTargets.map((target) => target.object),
      false
    );
    const hoveredObject = intersections[0]?.object;
    const target = hoverTargets.find(
      (candidate) => candidate.object === hoveredObject
    );

    if (!target) {
      hideTooltip();
      return;
    }

    showTooltipAt(position, target.type, target.item);
  }

  function hoveredTargetAt(event: MouseEvent | PointerEvent): HoverTarget | null {
    const position = pointerPosition(event);
    if (!position || !cameraRef || hoverTargets.length === 0) return null;

    const bounds = sceneShell.getBoundingClientRect();
    pointer.set(
      (position.x / bounds.width) * 2 - 1,
      -(position.y / bounds.height) * 2 + 1
    );
    cameraRef.updateMatrixWorld();
    raycaster.setFromCamera(pointer, cameraRef);

    const intersections = raycaster.intersectObjects(
      hoverTargets.map((target) => target.object),
      false
    );
    const hoveredObject = intersections[0]?.object;
    return (
      hoverTargets.find((candidate) => candidate.object === hoveredObject) ??
      null
    );
  }

  function handleSceneClick(event: MouseEvent): void {
    const target = hoveredTargetAt(event);
    if (!target) return;
    select(target.type, target.item.id, target.item.name);
  }

  function waterShape(river: RiverSection): THREE.Shape {
    const radius = channelRadius();
    const fillY = waterSurfaceY(river);
    const halfWidth = Math.sqrt(Math.max(0, radius * radius - fillY * fillY));
    const shape = new THREE.Shape();
    const segmentCount = 24;

    shape.moveTo(-halfWidth, fillY);
    shape.lineTo(halfWidth, fillY);

    for (let index = 0; index <= segmentCount; index += 1) {
      const z = halfWidth - (index / segmentCount) * halfWidth * 2;
      const y = -Math.sqrt(Math.max(0, radius * radius - z * z));
      shape.lineTo(z, y);
    }

    shape.closePath();
    return shape;
  }

  function waterSurfaceY(river: RiverSection): number {
    const radius = channelRadius();
    const fillRatio = riverFillPercent(river) / 100;
    return -radius + radius * fillRatio;
  }

  function waterSurfaceWidth(river: RiverSection): number {
    const radius = channelRadius();
    const fillY = waterSurfaceY(river);
    const halfWidth = Math.sqrt(Math.max(0, radius * radius - fillY * fillY));
    return Math.max(halfWidth * 2, 0.2);
  }
</script>

<div
  class="scene-shell"
  bind:this={sceneShell}
  role="application"
  aria-label="Interactive 3D region scene"
  on:pointermove={handleScenePointerMove}
  on:pointerleave={hideTooltip}
  on:click={handleSceneClick}
>
  <Canvas>
    <T.PerspectiveCamera
      bind:ref={cameraRef}
      makeDefault
      position={[10, 6.2, 13.5]}
      fov={48}
    >
      <OrbitRig target={[0, 0.05, 0]} minDistance={4.5} maxDistance={42} />
    </T.PerspectiveCamera>
    <T.Mesh>
      <T.SphereGeometry args={[82, 64, 32]} />
      <T.MeshBasicMaterial color="#9fc9d7" side={THREE.BackSide} />
    </T.Mesh>
    <T.Mesh position={[4, 8.8, -17]}>
      <T.SphereGeometry args={[1.8, 36, 18]} />
      <T.MeshBasicMaterial color="#ffe8a2" />
    </T.Mesh>
    <T.Mesh position={[4, 8.8, -17]}>
      <T.RingGeometry args={[2.1, 2.55, 36]} />
      <T.MeshBasicMaterial color="#ffe8a2" transparent opacity={0.32} />
    </T.Mesh>
    <T.PointLight position={[4, 8.8, -17]} intensity={1.1} distance={90} />
    {#each cloudPositions() as cloud}
      <T.Group position={[cloud[0], cloud[1], cloud[2]]} scale={cloud[3]}>
        <T.Mesh position={[-1.05, 0, 0]}>
          <T.SphereGeometry args={[1.35, 20, 12]} />
          <T.MeshBasicMaterial color="#eef4ee" transparent opacity={0.78} />
        </T.Mesh>
        <T.Mesh position={[0.2, 0.2, 0]}>
          <T.SphereGeometry args={[1.7, 20, 12]} />
          <T.MeshBasicMaterial color="#f7fbf7" transparent opacity={0.8} />
        </T.Mesh>
        <T.Mesh position={[1.55, -0.05, 0]}>
          <T.SphereGeometry args={[1.18, 20, 12]} />
          <T.MeshBasicMaterial color="#e8f0ea" transparent opacity={0.72} />
        </T.Mesh>
        <T.Mesh position={[0.25, -0.55, 0]} scale={[2.6, 0.58, 0.9]}>
          <T.SphereGeometry args={[1, 20, 10]} />
          <T.MeshBasicMaterial color="#eef5ef" transparent opacity={0.68} />
        </T.Mesh>
      </T.Group>
    {/each}
    <T.Mesh position={[0, -0.38, -34]} rotation={[-Math.PI / 2, 0, 0]}>
      <T.PlaneGeometry args={[120, 52, 8, 8]} />
      <T.MeshStandardMaterial color="#526943" roughness={0.98} />
    </T.Mesh>
    <T.Mesh position={[0, -0.39, 24]} rotation={[-Math.PI / 2, 0, 0]}>
      <T.PlaneGeometry args={[120, 42, 8, 4]} />
      <T.MeshStandardMaterial color="#425b39" roughness={0.98} />
    </T.Mesh>
    <T.Mesh position={[-28, 1.2, -34]} rotation={[0, 0.08, 0]}>
      <T.ConeGeometry args={[16, 4.2, 5]} />
      <T.MeshStandardMaterial color="#65785c" roughness={0.94} />
    </T.Mesh>
    <T.Mesh position={[-8, 1.45, -37]} rotation={[0, -0.16, 0]}>
      <T.ConeGeometry args={[19, 4.8, 5]} />
      <T.MeshStandardMaterial color="#596d54" roughness={0.94} />
    </T.Mesh>
    <T.Mesh position={[18, 1.2, -35]} rotation={[0, 0.1, 0]}>
      <T.ConeGeometry args={[16, 4.1, 5]} />
      <T.MeshStandardMaterial color="#718062" roughness={0.94} />
    </T.Mesh>
    <T.Mesh position={[39, 1.0, -32]} rotation={[0, -0.2, 0]}>
      <T.ConeGeometry args={[13, 3.4, 5]} />
      <T.MeshStandardMaterial color="#66765a" roughness={0.94} />
    </T.Mesh>
    <T.AmbientLight intensity={0.74} />
    <T.DirectionalLight position={[22, 18, 12]} intensity={1.75} />
    <T.HemisphereLight args={['#d9f5ff', '#455235', 0.76]} />

    {#if focusLocationType === 'reservoir'}
      {#each reservoirGroundPanels() as panel}
        <T.Mesh
          position={[panel.x, -0.04, panel.z]}
          rotation={[-Math.PI / 2, 0, 0]}
        >
          <T.PlaneGeometry args={[panel.width, panel.depth]} />
          <T.MeshStandardMaterial color={panel.color} roughness={0.94} />
        </T.Mesh>
      {/each}
      <T.Mesh position={[0, -0.035, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <T.RingGeometry args={[3.31, 5.45, 72]} />
        <T.MeshStandardMaterial color="#3c5237" roughness={0.94} />
      </T.Mesh>
      <T.Mesh
        position={[reservoirInletX(), -0.015, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <T.PlaneGeometry args={[reservoirInletLength() + 0.55, 1.62]} />
        <T.MeshStandardMaterial color="#665f43" roughness={0.9} />
      </T.Mesh>
      <T.Mesh
        position={[reservoirInletStartX(), -0.014, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <T.PlaneGeometry args={[1.45, 2.05]} />
        <T.MeshStandardMaterial color="#665f43" roughness={0.9} />
      </T.Mesh>
      <T.Mesh
        position={[reservoirInletX(), -0.005, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <T.PlaneGeometry
          args={[reservoirInletLength(), reservoirInletWidth()]}
        />
        <T.MeshStandardMaterial color="#20575b" transparent opacity={0.66} />
      </T.Mesh>
      <FlowingRiverSurface
        length={reservoirInletLength()}
        width={reservoirInletWidth()}
        surfaceY={0.02}
        x={reservoirInletX()}
        z={0}
        selected={true}
      />
      <T.Mesh position={[0, -0.02, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <T.RingGeometry args={[2.65, 3.35, 72]} />
        <T.MeshStandardMaterial color="#756e55" roughness={0.88} />
      </T.Mesh>
      <T.Mesh position={[0, focusedReservoirWaterSideY(), 0]}>
        <T.CylinderGeometry
          args={[
            focusedReservoir ? reservoirWaterRadius(focusedReservoir) : 2.58,
            2.84,
            focusedReservoirWaterSideHeight(),
            72,
            1,
            true
          ]}
        />
        <T.MeshStandardMaterial
          color="#2f9ed2"
          roughness={0.44}
          metalness={0.02}
          side={THREE.DoubleSide}
        />
      </T.Mesh>
      <T.Mesh position={[0, -1.03, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <T.CircleGeometry args={[2.84, 72]} />
        <T.MeshStandardMaterial color="#247b91" roughness={0.76} />
      </T.Mesh>
      <T.Mesh position={[-2.72, 0.24, 0]}>
        <T.BoxGeometry args={[0.2, 0.52, 1.35]} />
        <T.MeshStandardMaterial
          color="#8b7752"
          roughness={0.62}
          metalness={0.08}
        />
      </T.Mesh>
    {:else}
      <T.Group position={[0, -0.1, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <T.Mesh position={[0, channelRadius() + 0.28 + bankDepth() / 2, 0]}>
          <T.PlaneGeometry args={[channelLength(), bankDepth()]} />
          <T.MeshStandardMaterial color="#344a34" roughness={0.93} />
        </T.Mesh>
        <T.Mesh position={[0, -(channelRadius() + 0.28 + bankDepth() / 2), 0]}>
          <T.PlaneGeometry args={[channelLength(), bankDepth()]} />
          <T.MeshStandardMaterial color="#3d4d31" roughness={0.93} />
        </T.Mesh>
        <T.Mesh position={[0, channelRadius() + 0.14, 0]}>
          <T.PlaneGeometry args={[channelLength(), 0.28]} />
          <T.MeshStandardMaterial color="#6c6143" roughness={0.94} />
        </T.Mesh>
        <T.Mesh position={[0, -(channelRadius() + 0.14), 0]}>
          <T.PlaneGeometry args={[channelLength(), 0.28]} />
          <T.MeshStandardMaterial color="#665c3f" roughness={0.94} />
        </T.Mesh>
      </T.Group>

      {#each sceneryPositions(1) as item, index}
        <T.Group position={item}>
          <T.Mesh rotation={[0, index * 0.42, 0]}>
            <T.ConeGeometry args={[0.18 + (index % 3) * 0.04, 0.8, 7]} />
            <T.MeshStandardMaterial color="#51724c" roughness={0.9} />
          </T.Mesh>
          <T.Mesh position={[0.34, -0.05, -0.18]} scale={[1.7, 0.42, 1.0]}>
            <T.SphereGeometry args={[0.18 + (index % 2) * 0.06, 10, 6]} />
            <T.MeshStandardMaterial color="#716b50" roughness={0.96} />
          </T.Mesh>
        </T.Group>
      {/each}

      {#each sceneryPositions(-1) as item, index}
        <T.Group position={item}>
          <T.Mesh rotation={[0, -index * 0.36, 0]}>
            <T.ConeGeometry args={[0.2 + (index % 2) * 0.05, 0.72, 7]} />
            <T.MeshStandardMaterial color="#476a46" roughness={0.9} />
          </T.Mesh>
          <T.Mesh position={[-0.32, -0.05, 0.16]} scale={[1.5, 0.38, 0.95]}>
            <T.SphereGeometry args={[0.18 + (index % 3) * 0.04, 10, 6]} />
            <T.MeshStandardMaterial color="#807258" roughness={0.96} />
          </T.Mesh>
        </T.Group>
      {/each}

      <T.Mesh position={[0, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
        <T.CylinderGeometry
          args={[
            channelRadius(),
            channelRadius(),
            channelLength(),
            48,
            1,
            true,
            0,
            Math.PI
          ]}
        />
        <T.MeshStandardMaterial
          color="#6f6749"
          roughness={0.88}
          metalness={0.02}
          side={THREE.DoubleSide}
        />
      </T.Mesh>

      {#each scene.river_sections as river}
        <FlowingRiverSurface
          length={channelLength()}
          width={waterSurfaceWidth(river)}
          surfaceY={waterSurfaceY(river)}
          shape={waterShape(river)}
          selected={isSelected('river_section', river.id)}
          onCreate={(object) =>
            registerHoverTarget(object, 'river_section', river)}
        />
      {/each}
    {/if}

    {#each scene.gates as gate, index}
      <T.Group
        position={focusLocationType === 'reservoir'
          ? reservoirGatePosition(index)
          : [px(gate.x), 0.62, py(gate.y)]}
      >
        <T.Mesh
          onclick={() => select('gate', gate.id, gate.name)}
          oncreate={(object) => registerHoverTarget(object, 'gate', gate)}
        >
          <T.BoxGeometry args={[0.22, 1.35, 2.6]} />
          <T.MeshStandardMaterial
            color={isSelected('gate', gate.id) ? '#ffe08a' : '#d7b35a'}
            metalness={0.35}
            roughness={0.42}
          />
        </T.Mesh>
        {#if focusLocationType === 'reservoir'}
          <T.Mesh
            position={[-0.13, -0.03, 0]}
            onclick={() => select('gate', gate.id, gate.name)}
            oncreate={(object) => registerHoverTarget(object, 'gate', gate)}
          >
            <T.BoxGeometry args={[0.08, 0.86, 2.15]} />
            <T.MeshStandardMaterial
              color={isSelected('gate', gate.id) ? '#ffe08a' : '#b9974c'}
              metalness={0.18}
              roughness={0.48}
            />
          </T.Mesh>
          <T.Mesh
            position={[-0.18, -0.06, 0]}
            onclick={() => select('gate', gate.id, gate.name)}
            oncreate={(object) => registerHoverTarget(object, 'gate', gate)}
          >
            <T.BoxGeometry args={[0.04, 0.18, 1.78]} />
            <T.MeshStandardMaterial color="#121a1c" metalness={0.28} />
          </T.Mesh>
        {/if}
        <T.Mesh
          position={[0, -0.35 + gate.opening_percent / 120, 0]}
          onclick={() => select('gate', gate.id, gate.name)}
          oncreate={(object) => registerHoverTarget(object, 'gate', gate)}
        >
          <T.BoxGeometry args={[0.34, 0.22, 2.25]} />
          <T.MeshStandardMaterial color="#222b2d" metalness={0.25} />
        </T.Mesh>
      </T.Group>
    {/each}

    {#each scene.sensors as sensor, index}
      <T.Group
        position={focusLocationType === 'reservoir'
          ? reservoirSensorPosition(index)
          : [px(sensor.x), 0.72, py(sensor.y)]}
      >
        <T.Mesh
          onclick={() => select('sensor', sensor.id, sensor.name)}
          oncreate={(object) => registerHoverTarget(object, 'sensor', sensor)}
        >
          <T.SphereGeometry
            args={[isSelected('sensor', sensor.id) ? 0.22 : 0.17, 24, 16]}
          />
          <T.MeshStandardMaterial
            color={sensor.health === 'critical' ? '#ff5a4f' : '#64d2ff'}
            emissive={sensor.health === 'critical' ? '#ff5a4f' : '#1e85b7'}
            emissiveIntensity={isSelected('sensor', sensor.id) ? 1.2 : 0.55}
          />
        </T.Mesh>
        <T.Mesh
          position={[0, -0.32, 0]}
          onclick={() => select('sensor', sensor.id, sensor.name)}
          oncreate={(object) => registerHoverTarget(object, 'sensor', sensor)}
        >
          <T.CylinderGeometry args={[0.035, 0.035, 0.58, 10]} />
          <T.MeshStandardMaterial color="#c7d2cc" />
        </T.Mesh>
      </T.Group>
    {/each}

    {#each scene.reservoirs as reservoir}
      <T.Group position={reservoirPosition(reservoir)}>
        {#if focusLocationType !== 'reservoir'}
          <T.Mesh position={[0, -0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <T.CircleGeometry args={[1.04, 48]} />
            <T.MeshStandardMaterial color="#756d50" roughness={0.9} />
          </T.Mesh>
          <T.Mesh position={[0, -0.035, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <T.CircleGeometry args={[0.82, 48]} />
            <T.MeshStandardMaterial
              color="#57bdd5"
              emissive="#17738f"
              emissiveIntensity={0.22}
              transparent
              opacity={0.82}
              roughness={0.34}
            />
          </T.Mesh>
          <T.Mesh
            position={[0, -0.02, 0]}
            onclick={() => select('reservoir', reservoir.id, reservoir.name)}
            oncreate={(object) =>
              registerHoverTarget(object, 'reservoir', reservoir)}
          >
            <T.CylinderGeometry args={[0.83, 0.83, 0.08, 48, 1, true]} />
            <T.MeshStandardMaterial
              color={isSelected('reservoir', reservoir.id)
                ? '#5ec9e4'
                : '#3f8ead'}
              roughness={0.42}
              metalness={0.04}
            />
          </T.Mesh>
        {:else}
          <T.Mesh
            onclick={() => select('reservoir', reservoir.id, reservoir.name)}
            oncreate={(object) =>
              registerHoverTarget(object, 'reservoir', reservoir)}
          >
            <T.CylinderGeometry
              args={[
                reservoirRadius(reservoir),
                reservoirRadius(reservoir),
                reservoir.id === focusLocationId ? 0.92 : 0.22,
                40,
                1,
                true
              ]}
            />
            <T.MeshStandardMaterial
              color={isSelected('reservoir', reservoir.id)
                ? '#2f9ed2'
                : '#2d8fb8'}
              roughness={0.42}
              metalness={0.08}
            />
          </T.Mesh>
          <T.Mesh
            position={[0, reservoirWaterSurfaceY(reservoir), 0]}
            rotation={[-Math.PI / 2, 0, 0]}
            onclick={() => select('reservoir', reservoir.id, reservoir.name)}
            oncreate={(object) =>
              registerHoverTarget(object, 'reservoir', reservoir)}
          >
            <T.CircleGeometry args={[reservoirWaterRadius(reservoir), 72]} />
            <T.MeshStandardMaterial
              color="#2f9ed2"
              depthWrite={false}
              opacity={0.94}
            />
          </T.Mesh>
        {/if}
      </T.Group>
    {/each}

    {#each scene.vegetation_zones as vegetation, index}
      <T.Group
        position={focusLocationType === 'reservoir'
          ? reservoirVegetationPosition(index)
          : [px(vegetation.x), 0.26, py(vegetation.y)]}
      >
        <T.Mesh
          onclick={() =>
            select('vegetation_zone', vegetation.id, vegetation.name)}
          oncreate={(object) =>
            registerHoverTarget(object, 'vegetation_zone', vegetation)}
        >
          <T.ConeGeometry args={[0.28, 0.72, 8]} />
          <T.MeshStandardMaterial
            color={vegetation.risk_level === 'yellow' ? '#d7c65d' : '#4da86b'}
            emissive={isSelected('vegetation_zone', vegetation.id)
              ? '#607b34'
              : '#000000'}
            emissiveIntensity={0.45}
          />
        </T.Mesh>
      </T.Group>
    {/each}

  </Canvas>

  <div class="hud">
    <strong>{scene.region.name}</strong>
    <span>{scene.notifications.length} active notifications</span>
  </div>

  {#if tooltip}
    <div
      bind:this={tooltipElement}
      class="object-tooltip"
      style={`left:${tooltip.x}px; top:${tooltip.y}px;`}
    >
      <p>{tooltip.type}</p>
      <strong>{tooltip.title}</strong>
      <dl>
        {#each tooltip.rows.slice(0, 9) as row}
          <div>
            <dt>{row.label}</dt>
            <dd>{row.value}</dd>
          </div>
        {/each}
      </dl>
    </div>
  {/if}
</div>

<style>
  .scene-shell {
    position: absolute;
    inset: 0;
  }

  .scene-shell :global(canvas) {
    width: 100%;
    height: 100%;
  }

  .hud {
    position: absolute;
    left: 22px;
    bottom: 22px;
    display: flex;
    gap: 12px;
    align-items: center;
    border: 1px solid rgba(180, 212, 203, 0.22);
    border-radius: 8px;
    background: rgba(13, 20, 22, 0.72);
    padding: 10px 12px;
    color: #dce8e3;
    pointer-events: none;
  }

  .hud span {
    color: #9fb1ab;
  }

  .object-tooltip {
    position: absolute;
    z-index: 6;
    width: min(320px, calc(100% - 32px));
    max-width: 320px;
    box-sizing: border-box;
    border: 1px solid rgba(193, 226, 218, 0.28);
    border-radius: 8px;
    background: rgba(11, 17, 19, 0.9);
    box-shadow: 0 16px 42px rgba(0, 0, 0, 0.36);
    color: #edf3ee;
    padding: 10px 12px;
    pointer-events: none;
    backdrop-filter: blur(10px);
  }

  .object-tooltip p {
    margin: 0 0 3px;
    color: #9fb1ab;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0;
    text-transform: uppercase;
  }

  .object-tooltip strong {
    display: block;
    margin-bottom: 8px;
  }

  .object-tooltip dl {
    display: grid;
    gap: 5px;
    margin: 0;
  }

  .object-tooltip div {
    display: grid;
    grid-template-columns: minmax(86px, 0.8fr) minmax(0, 1fr);
    gap: 10px;
  }

  .object-tooltip dt {
    overflow-wrap: anywhere;
    color: #9fb1ab;
    font-size: 0.76rem;
    text-transform: capitalize;
  }

  .object-tooltip dd {
    margin: 0;
    overflow-wrap: anywhere;
    color: #edf3ee;
    font-size: 0.76rem;
    text-align: right;
  }
</style>
