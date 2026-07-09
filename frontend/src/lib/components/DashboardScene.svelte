<script lang="ts">
  import { Canvas, T } from '@threlte/core';
  import OrbitRig from './OrbitRig.svelte';
  import { notificationSeverityForRegion, severityColor } from '$lib/display';
  import type { Notification, Region } from '$lib/types';

  export let regions: Region[];
  export let notifications: Notification[];
  export let selectedRegionId: number | null;
  export let onSelectRegion: (region: Region) => void;
  export let onEnterRegion: (region: Region) => void;

  function x(mapX: number): number {
    return (mapX - 0.5) * 12;
  }

  function z(mapY: number): number {
    return (mapY - 0.5) * 7;
  }

  function beaconHeight(region: Region): number {
    const severity = notificationSeverityForRegion(region, notifications);
    if (severity === 'red') return 1.2;
    if (severity === 'yellow') return 0.85;
    return 0.5;
  }
</script>

<div class="scene-shell">
  <Canvas>
    <T.PerspectiveCamera makeDefault position={[0, 8, 8]} fov={42}>
      <OrbitRig target={[0, 0, 0]} maxPolarAngle={1.35} minDistance={5} maxDistance={16} />
    </T.PerspectiveCamera>
    <T.AmbientLight intensity={0.75} />
    <T.DirectionalLight position={[4, 7, 5]} intensity={1.3} />

    <T.Mesh rotation={[-Math.PI / 2.7, 0, 0]} position={[0, -0.05, 0]}>
      <T.PlaneGeometry args={[13, 8, 18, 12]} />
      <T.MeshStandardMaterial color="#2f6f68" roughness={0.82} metalness={0.05} />
    </T.Mesh>

    <T.GridHelper args={[13, 13, '#9fc8bd', '#3d5d57']} position={[0, 0.01, 0]} />

    {#each regions as region}
      {@const severity = notificationSeverityForRegion(region, notifications)}
      {@const selected = selectedRegionId === region.id}
      <T.Mesh
        position={[x(region.map_x), beaconHeight(region), z(region.map_y)]}
        onclick={() => onSelectRegion(region)}
        ondoubleclick={() => onEnterRegion(region)}
      >
        <T.SphereGeometry args={[selected ? 0.34 : 0.26, 32, 16]} />
        <T.MeshStandardMaterial
          color={severityColor[severity]}
          emissive={severityColor[severity]}
          emissiveIntensity={selected ? 1.4 : 0.75}
          transparent
          opacity={0.82}
        />
      </T.Mesh>
      <T.Mesh position={[x(region.map_x), 0.06, z(region.map_y)]} rotation={[-Math.PI / 2, 0, 0]}>
        <T.CircleGeometry args={[selected ? 0.78 : 0.55, 36]} />
        <T.MeshBasicMaterial color={severityColor[severity]} transparent opacity={selected ? 0.34 : 0.2} />
      </T.Mesh>
      <T.Mesh position={[x(region.map_x), beaconHeight(region) / 2, z(region.map_y)]}>
        <T.CylinderGeometry args={[0.03, 0.03, beaconHeight(region), 12]} />
        <T.MeshStandardMaterial color={severityColor[severity]} transparent opacity={0.38} />
      </T.Mesh>
    {/each}
  </Canvas>

  <div class="hud">
    <p>Double-click a beacon to enter a region. Orbit, pan, and zoom are enabled.</p>
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
    margin: 0;
  }
</style>
