<script lang="ts">
  import { onMount } from 'svelte';
  import { useThrelte } from '@threlte/core';
  import * as THREE from 'three';
  import { getTopographicMapAsset } from '$lib/api';

  const fallbackMapUrl = '/maps/murrumbidgee-opentopomap-z10.png';
  const mapWidth = 18;
  const mapDepth = 12;
  const surroundingGroundWidth = 34;
  const surroundingGroundDepth = 26;

  const { invalidate, scene } = useThrelte();

  onMount(() => {
    const surroundingGroundGeometry = new THREE.PlaneGeometry(
      surroundingGroundWidth,
      surroundingGroundDepth,
      1,
      1
    );
    const surroundingGroundMaterial = new THREE.MeshBasicMaterial({
      color: '#6ea15f'
    });
    const surroundingGroundMesh = new THREE.Mesh(
      surroundingGroundGeometry,
      surroundingGroundMaterial
    );
    const geometry = new THREE.PlaneGeometry(mapWidth, mapDepth, 18, 12);
    const material = new THREE.MeshBasicMaterial({ color: '#2f6f68' });
    const mesh = new THREE.Mesh(geometry, material);
    const loader = new THREE.TextureLoader();

    surroundingGroundMesh.position.set(0, -0.065, 0);
    surroundingGroundMesh.rotation.set(-Math.PI / 2, 0, 0);
    surroundingGroundMesh.raycast = () => {};
    mesh.position.set(0, -0.05, 0);
    mesh.rotation.set(-Math.PI / 2, 0, 0);
    mesh.raycast = () => {};
    scene.add(surroundingGroundMesh);
    scene.add(mesh);
    invalidate();

    loader.setCrossOrigin('anonymous');

    let mounted = true;
    let texture: THREE.Texture | null = null;

    const loadTexture = (url: string) => {
      if (!mounted) return;
      texture = loader.load(url, (loadedTexture) => {
        if (!mounted) {
          loadedTexture.dispose();
          return;
        }
        loadedTexture.colorSpace = THREE.SRGBColorSpace;
        loadedTexture.anisotropy = 4;
        material.color.set('#ffffff');
        material.map = loadedTexture;
        material.needsUpdate = true;
        invalidate();
      });
    };

    getTopographicMapAsset()
      .then((asset) => loadTexture(asset.url))
      .catch(() => loadTexture(fallbackMapUrl));

    return () => {
      mounted = false;
      scene.remove(surroundingGroundMesh);
      scene.remove(mesh);
      texture?.dispose();
      surroundingGroundMaterial.dispose();
      surroundingGroundGeometry.dispose();
      material.dispose();
      geometry.dispose();
    };
  });
</script>
