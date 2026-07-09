<script lang="ts">
  import { Canvas, T } from '@threlte/core';
  import DashboardHitProjector from './DashboardHitProjector.svelte';
  import OrbitRig from './OrbitRig.svelte';
  import TopographicGround from './TopographicGround.svelte';
  import { severityColor } from '$lib/display';
  import type { DashboardLocation, Notification } from '$lib/types';
  import type { HitPosition } from './DashboardHitProjector.svelte';

  export let locations: DashboardLocation[];
  export let selectedLocationKey: string | null;
  export let focusedLocationKey: string | null = null;
  export let focusedNotification: Notification | null = null;
  export let onSelectLocation: (location: DashboardLocation) => void;
  export let onEnterLocation: (location: DashboardLocation) => void;
  export let onHoverLocation: (location: DashboardLocation) => void;
  export let onClearHoveredLocation: () => void;
  export let onPrefetchLocation: (location: DashboardLocation) => void;

  const mapWidth = 18;
  const mapDepth = 12;
  let hitPositions: Record<string, HitPosition> = {};

  function x(mapX: number): number {
    return (mapX - 0.5) * mapWidth;
  }

  function z(mapY: number): number {
    return (mapY - 0.5) * mapDepth;
  }

  function key(location: DashboardLocation): string {
    return `${location.type}:${location.id}`;
  }

  function beaconHeight(location: DashboardLocation): number {
    if (location.severity === 'red') return 1.2;
    if (location.severity === 'yellow') return 0.85;
    return 0.5;
  }

  function notificationFocusHeight(notification: Notification): number {
    if (notification.severity === 'red') return 1.8;
    if (notification.severity === 'yellow') return 1.45;
    return 1.1;
  }

  function activateLocation(location: DashboardLocation): void {
    onSelectLocation(location);
    void onEnterLocation(location);
  }

  function hoverLocation(location: DashboardLocation): void {
    onHoverLocation(location);
    onPrefetchLocation(location);
  }

  function markerPosition(location: DashboardLocation): [number, number, number] {
    return [x(location.map_x), beaconHeight(location), z(location.map_y)];
  }
</script>

<div class="scene-shell">
  <Canvas>
    <T.PerspectiveCamera makeDefault position={[0, 13.5, 9.5]} fov={50}>
      <OrbitRig
        target={[0, 0, 0.9]}
        maxPolarAngle={1.25}
        minDistance={5}
        maxDistance={34}
      />
    </T.PerspectiveCamera>
    <T.AmbientLight intensity={0.75} />
    <T.DirectionalLight position={[4, 7, 5]} intensity={1.3} />

    <TopographicGround />

    <DashboardHitProjector
      {locations}
      locationKey={key}
      locationPosition={markerPosition}
      onPositions={(positions) => (hitPositions = positions)}
    />

    {#each locations as location}
      {@const severity = location.severity}
      {@const selected = selectedLocationKey === key(location)}
      {@const focused = focusedLocationKey === key(location)}
      {@const emphasized = selected || focused}
      <T.Mesh
        position={[x(location.map_x), 0.11, z(location.map_y)]}
        rotation={[-Math.PI / 2, 0, 0]}
        onclick={() => activateLocation(location)}
        onpointerenter={() => hoverLocation(location)}
        onpointerleave={onClearHoveredLocation}
      >
        <T.CircleGeometry args={[1.05, 36]} />
        <T.MeshBasicMaterial
          color="#ffffff"
          depthWrite={false}
          transparent
          opacity={0.001}
        />
      </T.Mesh>
      <T.Mesh
        position={[x(location.map_x), 0.052, z(location.map_y)]}
        rotation={[-Math.PI / 2, 0, 0]}
        onclick={() => activateLocation(location)}
        onpointerenter={() => hoverLocation(location)}
        onpointerleave={onClearHoveredLocation}
      >
        <T.CircleGeometry args={[emphasized ? 0.9 : 0.66, 36]} />
        <T.MeshBasicMaterial
          color="#05090a"
          transparent
          opacity={emphasized ? 0.34 : 0.26}
        />
      </T.Mesh>
      <T.Mesh
        position={[x(location.map_x), 0.064, z(location.map_y)]}
        rotation={[-Math.PI / 2, 0, 0]}
        onclick={() => activateLocation(location)}
        onpointerenter={() => hoverLocation(location)}
        onpointerleave={onClearHoveredLocation}
      >
        <T.RingGeometry
          args={[emphasized ? 0.78 : 0.55, emphasized ? 0.86 : 0.62, 40]}
        />
        <T.MeshBasicMaterial color="#061012" transparent opacity={0.78} />
      </T.Mesh>
      <T.Mesh
        position={[
          x(location.map_x),
          beaconHeight(location),
          z(location.map_y)
        ]}
        onclick={() => activateLocation(location)}
        onpointerenter={() => hoverLocation(location)}
        onpointerleave={onClearHoveredLocation}
      >
        {#if location.type === 'reservoir'}
          <T.CylinderGeometry
            args={[
              emphasized ? 0.34 : 0.26,
              emphasized ? 0.34 : 0.26,
              0.24,
              32
            ]}
          />
        {:else}
          <T.SphereGeometry args={[emphasized ? 0.34 : 0.26, 32, 16]} />
        {/if}
        <T.MeshStandardMaterial
          color={severityColor[severity]}
          emissive={severityColor[severity]}
          emissiveIntensity={emphasized ? 1.4 : 0.75}
          transparent
          opacity={0.82}
        />
      </T.Mesh>
      <T.Mesh
        position={[x(location.map_x), 0.068, z(location.map_y)]}
        rotation={[-Math.PI / 2, 0, 0]}
        onclick={() => activateLocation(location)}
        onpointerenter={() => hoverLocation(location)}
        onpointerleave={onClearHoveredLocation}
      >
        <T.CircleGeometry args={[emphasized ? 0.78 : 0.55, 36]} />
        <T.MeshBasicMaterial
          color={severityColor[severity]}
          transparent
          opacity={emphasized ? 0.34 : 0.2}
        />
      </T.Mesh>
      <T.Mesh
        position={[
          x(location.map_x),
          beaconHeight(location) / 2,
          z(location.map_y)
        ]}
      >
        <T.CylinderGeometry args={[0.048, 0.048, beaconHeight(location), 12]} />
        <T.MeshBasicMaterial color="#05090a" transparent opacity={0.82} />
      </T.Mesh>
      <T.Mesh
        position={[
          x(location.map_x),
          beaconHeight(location) / 2,
          z(location.map_y)
        ]}
      >
        <T.CylinderGeometry args={[0.03, 0.03, beaconHeight(location), 12]} />
        <T.MeshStandardMaterial
          color={severityColor[severity]}
          transparent
          opacity={0.5}
        />
      </T.Mesh>
    {/each}

    {#if focusedNotification}
      {@const focusX = x(focusedNotification.map_x)}
      {@const focusZ = z(focusedNotification.map_y)}
      <T.Mesh
        position={[
          focusX,
          notificationFocusHeight(focusedNotification),
          focusZ
        ]}
        rotation={[0, 0, Math.PI / 4]}
      >
        <T.OctahedronGeometry args={[0.32, 0]} />
        <T.MeshStandardMaterial
          color={severityColor[focusedNotification.severity]}
          emissive={severityColor[focusedNotification.severity]}
          emissiveIntensity={1.8}
          transparent
          opacity={0.95}
        />
      </T.Mesh>
      <T.Mesh
        position={[focusX, 0.082, focusZ]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <T.RingGeometry args={[1.0, 1.12, 56]} />
        <T.MeshBasicMaterial
          color={severityColor[focusedNotification.severity]}
          transparent
          opacity={0.82}
        />
      </T.Mesh>
      <T.Mesh
        position={[focusX, 0.088, focusZ]}
        rotation={[-Math.PI / 2, 0, 0]}
      >
        <T.RingGeometry args={[1.32, 1.42, 56]} />
        <T.MeshBasicMaterial color="#edf3ee" transparent opacity={0.52} />
      </T.Mesh>
    {/if}
  </Canvas>

  <div class="hit-layer">
    {#each locations as location}
      {@const position = hitPositions[key(location)]}
      {#if position?.visible}
        <button
          class="location-hit"
          type="button"
          aria-label={`Open ${location.label}`}
          style={`left:${position.x}px; top:${position.y}px;`}
          on:click={() => activateLocation(location)}
          on:mouseenter={() => hoverLocation(location)}
          on:mouseleave={onClearHoveredLocation}
          on:focus={() => hoverLocation(location)}
          on:blur={onClearHoveredLocation}
        ></button>
      {/if}
    {/each}
  </div>

  <div class="hud">
    <p>Click a river or reservoir location to enter its local view.</p>
    <small
      >Map data: OpenStreetMap contributors, SRTM | Style: OpenTopoMap
      (CC-BY-SA)</small
    >
  </div>
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

  .hit-layer {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  .location-hit {
    position: absolute;
    width: 64px;
    height: 64px;
    border: 0;
    border-radius: 999px;
    background: transparent;
    cursor: pointer;
    pointer-events: auto;
    transform: translate(-50%, -50%);
  }

  .location-hit:focus-visible {
    outline: 2px solid #d7f3ea;
    outline-offset: 2px;
  }

  .hud {
    position: absolute;
    left: 22px;
    bottom: 22px;
    max-width: 420px;
    border: 1px solid rgba(180, 212, 203, 0.22);
    border-radius: 8px;
    background: rgba(13, 20, 22, 0.72);
    padding: 10px 12px;
    color: #c8d7d2;
    font-size: 0.86rem;
    pointer-events: none;
  }

  .hud p {
    margin: 0 0 4px;
  }

  .hud small {
    display: block;
    color: #9fb1ab;
    font-size: 0.72rem;
  }
</style>
