<script lang="ts">
  import { onMount } from 'svelte';
  import { useTask, useThrelte } from '@threlte/core';
  import * as THREE from 'three';

  export let length: number;
  export let width: number;
  export let surfaceY: number;
  export let shape: THREE.Shape | null = null;
  export let x = 0;
  export let z = 0;
  export let rotationY = 0;
  export let selected = false;
  export let onCreate:
    | ((object: THREE.Object3D) => (() => void) | void)
    | undefined = undefined;

  const { invalidate, scene } = useThrelte();
  let mesh: THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial> | null =
    null;
  let texture: THREE.CanvasTexture | null = null;
  let cleanupObject: (() => void) | void;

  function createFlowTexture(): THREE.CanvasTexture {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 128;

    const context = canvas.getContext('2d');
    if (context) {
      const gradient = context.createLinearGradient(0, 0, 0, canvas.height);
      gradient.addColorStop(0, 'rgba(47, 142, 158, 0.86)');
      gradient.addColorStop(0.5, 'rgba(38, 154, 176, 0.9)');
      gradient.addColorStop(1, 'rgba(36, 118, 142, 0.86)');
      context.fillStyle = gradient;
      context.fillRect(0, 0, canvas.width, canvas.height);

      for (let index = 0; index < 16; index += 1) {
        const y = 12 + ((index * 31) % 104);
        const x = (index * 41) % 512;
        const lineLength = 130 + (index % 4) * 38;
        context.strokeStyle =
          index % 3 === 0
            ? 'rgba(231, 252, 249, 0.42)'
            : 'rgba(132, 220, 223, 0.3)';
        context.lineWidth = index % 3 === 0 ? 3.5 : 2;
        context.beginPath();
        context.moveTo(x, y);
        context.bezierCurveTo(
          x + lineLength * 0.32,
          y - 7,
          x + lineLength * 0.72,
          y + 7,
          x + lineLength,
          y
        );
        context.stroke();
      }
    }

    const nextTexture = new THREE.CanvasTexture(canvas);
    nextTexture.colorSpace = THREE.SRGBColorSpace;
    nextTexture.wrapS = THREE.RepeatWrapping;
    nextTexture.wrapT = THREE.ClampToEdgeWrapping;
    nextTexture.repeat.set(Math.max(3.2, length / 7), 1);
    nextTexture.anisotropy = 4;
    return nextTexture;
  }

  function assignFlowUvs(geometry: THREE.BufferGeometry): void {
    const position = geometry.getAttribute('position');
    const uvs = new Float32Array(position.count * 2);
    const safeWidth = Math.max(width, 0.1);
    const safeLength = Math.max(length, 0.1);

    for (let index = 0; index < position.count; index += 1) {
      uvs[index * 2] = position.getZ(index) / safeLength;
      uvs[index * 2 + 1] = position.getX(index) / safeWidth + 0.5;
    }

    geometry.setAttribute('uv', new THREE.BufferAttribute(uvs, 2));
  }

  onMount(() => {
    texture = createFlowTexture();

    const geometry = shape
      ? new THREE.ExtrudeGeometry(shape, {
          depth: length,
          bevelEnabled: false,
          steps: 1
        })
      : new THREE.PlaneGeometry(length, Math.max(width, 0.1), 40, 4);

    if (shape) {
      assignFlowUvs(geometry);
    }

    const material = new THREE.MeshStandardMaterial({
      color: selected ? '#b9f1ec' : '#74c9c8',
      depthWrite: false,
      emissive: selected ? '#37b8bd' : '#197f8f',
      emissiveIntensity: selected ? 0.36 : 0.24,
      emissiveMap: texture,
      map: texture,
      metalness: 0.02,
      opacity: selected ? 0.68 : 0.6,
      roughness: 0.5,
      side: THREE.DoubleSide,
      transparent: true
    });

    mesh = new THREE.Mesh(geometry, material);
    if (shape) {
      mesh.position.set(x - length / 2, 0, z);
      mesh.rotation.set(0, Math.PI / 2 + rotationY, 0);
    } else {
      mesh.position.set(x, surfaceY + 0.035, z);
      mesh.rotation.set(-Math.PI / 2, rotationY, 0);
    }
    mesh.renderOrder = 2;
    scene.add(mesh);
    cleanupObject = onCreate?.(mesh);
    invalidate();

    return () => {
      cleanupObject?.();
      if (mesh) scene.remove(mesh);
      geometry.dispose();
      material.dispose();
      texture?.dispose();
    };
  });

  useTask((delta) => {
    if (!texture || !mesh) return;
    texture.offset.x -= delta * 0.09;
    texture.offset.y += delta * 0.012;
    texture.needsUpdate = true;
    mesh.material.opacity = selected ? 0.72 : 0.66;
    invalidate();
  });
</script>
