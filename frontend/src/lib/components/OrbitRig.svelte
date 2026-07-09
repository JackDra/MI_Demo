<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { useThrelte } from '@threlte/core';
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

  export let target: [number, number, number] = [0, 0, 0];
  export let minDistance = 4;
  export let maxDistance = 16;
  export let maxPolarAngle = Math.PI;

  const { camera, canvas, invalidate } = useThrelte();
  let controls: OrbitControls | null = null;

  onMount(() => {
    controls = new OrbitControls(camera.current, canvas);
    controls.enableDamping = true;
    controls.minDistance = minDistance;
    controls.maxDistance = maxDistance;
    controls.maxPolarAngle = maxPolarAngle;
    controls.target.set(...target);
    controls.addEventListener('change', invalidate);
    controls.update();

    return () => {
      controls?.removeEventListener('change', invalidate);
      controls?.dispose();
      controls = null;
    };
  });

  onDestroy(() => {
    controls?.dispose();
  });
</script>
