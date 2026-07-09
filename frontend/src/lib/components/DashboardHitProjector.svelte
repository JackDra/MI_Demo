<script context="module" lang="ts">
  export type HitPosition = {
    x: number;
    y: number;
    visible: boolean;
  };
</script>

<script lang="ts">
  import { useTask, useThrelte } from '@threlte/core';
  import * as THREE from 'three';
  import type { DashboardLocation } from '$lib/types';

  export let locations: DashboardLocation[];
  export let locationKey: (location: DashboardLocation) => string;
  export let locationPosition: (location: DashboardLocation) => [number, number, number];
  export let onPositions: (positions: Record<string, HitPosition>) => void;

  const { camera, canvas } = useThrelte();
  const projected = new THREE.Vector3();
  let lastSignature = '';

  useTask(() => {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const positions: Record<string, HitPosition> = {};

    for (const location of locations) {
      projected.set(...locationPosition(location)).project(camera.current);
      const x = ((projected.x + 1) / 2) * width;
      const y = ((1 - projected.y) / 2) * height;
      positions[locationKey(location)] = {
        x,
        y,
        visible:
          projected.z > -1 &&
          projected.z < 1 &&
          x >= -48 &&
          x <= width + 48 &&
          y >= -48 &&
          y <= height + 48
      };
    }

    const signature = Object.entries(positions)
      .map(
        ([key, position]) =>
          `${key}:${Math.round(position.x)}:${Math.round(position.y)}:${position.visible}`
      )
      .join('|');

    if (signature !== lastSignature) {
      lastSignature = signature;
      onPositions(positions);
    }
  });
</script>
