<script lang="ts">
  import { Canvas, T } from '@threlte/core';
  import OrbitRig from './OrbitRig.svelte';
  import type { ScenePayload, SelectableComponent } from '$lib/types';

  export let scene: ScenePayload;
  export let selectedComponentKey: string | null;
  export let onSelectComponent: (component: SelectableComponent) => void;

  function key(type: string, id: number): string {
    return `${type}:${id}`;
  }

  function isSelected(type: string, id: number): boolean {
    return selectedComponentKey === key(type, id);
  }

  function select(type: SelectableComponent['type'], id: number, label: string): void {
    onSelectComponent({ type, id, label } as SelectableComponent);
  }

  function channelLength(): number {
    return 9.5;
  }
</script>

<div class="scene-shell">
  <Canvas>
    <T.PerspectiveCamera makeDefault position={[6, 5, 8]} fov={48}>
      <OrbitRig target={[0, 0, 0]} minDistance={4} maxDistance={16} />
    </T.PerspectiveCamera>
    <T.AmbientLight intensity={0.65} />
    <T.DirectionalLight position={[5, 8, 4]} intensity={1.35} />
    <T.HemisphereLight args={['#d7fff5', '#26362e', 0.55]} />

    <T.Mesh position={[0, -0.18, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      <T.PlaneGeometry args={[12, 8]} />
      <T.MeshStandardMaterial color="#2f3d32" roughness={0.9} />
    </T.Mesh>

    <T.Mesh position={[0, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
      <T.CylinderGeometry args={[1.25, 1.25, channelLength(), 32, 1, true, 0, Math.PI]} />
      <T.MeshStandardMaterial color="#58635b" roughness={0.72} side={2} />
    </T.Mesh>

    {#each scene.river_sections as river}
      <T.Mesh
        position={[0, 0.04, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        onclick={() => select('river_section', river.id, river.name)}
      >
        <T.PlaneGeometry args={[channelLength(), 1.55, 24, 4]} />
        <T.MeshStandardMaterial
          color={isSelected('river_section', river.id) ? '#61d9ff' : '#2688c7'}
          emissive="#0a5d84"
          emissiveIntensity={0.35}
          transparent
          opacity={0.82}
        />
      </T.Mesh>
    {/each}

    {#each scene.gates as gate}
      <T.Group position={[gate.x, 0.62, gate.y]}>
        <T.Mesh onclick={() => select('gate', gate.id, gate.name)}>
          <T.BoxGeometry args={[0.22, 1.35, 2.6]} />
          <T.MeshStandardMaterial
            color={isSelected('gate', gate.id) ? '#ffe08a' : '#d7b35a'}
            metalness={0.35}
            roughness={0.42}
          />
        </T.Mesh>
        <T.Mesh position={[0, -0.35 + gate.opening_percent / 120, 0]}>
          <T.BoxGeometry args={[0.34, 0.22, 2.25]} />
          <T.MeshStandardMaterial color="#222b2d" metalness={0.25} />
        </T.Mesh>
      </T.Group>
    {/each}

    {#each scene.sensors as sensor}
      <T.Group position={[sensor.x, 0.72, sensor.y]}>
        <T.Mesh onclick={() => select('sensor', sensor.id, sensor.name)}>
          <T.SphereGeometry args={[isSelected('sensor', sensor.id) ? 0.22 : 0.17, 24, 16]} />
          <T.MeshStandardMaterial
            color={sensor.health === 'critical' ? '#ff5a4f' : '#64d2ff'}
            emissive={sensor.health === 'critical' ? '#ff5a4f' : '#1e85b7'}
            emissiveIntensity={isSelected('sensor', sensor.id) ? 1.2 : 0.55}
          />
        </T.Mesh>
        <T.Mesh position={[0, -0.32, 0]}>
          <T.CylinderGeometry args={[0.035, 0.035, 0.58, 10]} />
          <T.MeshStandardMaterial color="#c7d2cc" />
        </T.Mesh>
      </T.Group>
    {/each}

    {#each scene.reservoirs as reservoir}
      <T.Group position={[reservoir.x, 0.16, reservoir.y]}>
        <T.Mesh onclick={() => select('reservoir', reservoir.id, reservoir.name)}>
          <T.CylinderGeometry args={[0.55, 0.55, 0.22, 32]} />
          <T.MeshStandardMaterial color={isSelected('reservoir', reservoir.id) ? '#7cdfff' : '#477d9d'} />
        </T.Mesh>
        <T.Mesh position={[0, 0.2, 0]}>
          <T.CylinderGeometry args={[0.5, 0.5, 0.1, 32]} />
          <T.MeshStandardMaterial color="#2f9ed2" transparent opacity={0.68} />
        </T.Mesh>
      </T.Group>
    {/each}

    {#each scene.vegetation_zones as vegetation}
      <T.Group position={[vegetation.x, 0.26, vegetation.y]}>
        <T.Mesh onclick={() => select('vegetation_zone', vegetation.id, vegetation.name)}>
          <T.ConeGeometry args={[0.28, 0.72, 8]} />
          <T.MeshStandardMaterial
            color={vegetation.risk_level === 'yellow' ? '#d7c65d' : '#4da86b'}
            emissive={isSelected('vegetation_zone', vegetation.id) ? '#607b34' : '#000000'}
            emissiveIntensity={0.45}
          />
        </T.Mesh>
      </T.Group>
    {/each}

    <T.GridHelper args={[12, 12, '#86978d', '#405149']} position={[0, -0.16, 0]} />
  </Canvas>

  <div class="hud">
    <strong>{scene.region.name}</strong>
    <span>{scene.notifications.length} active notifications</span>
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
</style>
