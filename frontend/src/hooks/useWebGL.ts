import { useEffect, useRef, useCallback } from 'react';
import * as THREE from 'three';
import { useDesignStore } from '@/store/designStore';
import type { DesignComponent, DesignEdge } from '@/types/design';

const COMPONENT_COLORS: Record<string, number> = {
  api_gateway:   0x6366f1,
  microservice:  0x22d3ee,
  database:      0x34d399,
  cache:         0xfbbf24,
  queue:         0xf97316,
  load_balancer: 0xa78bfa,
  cdn:           0xfb7185,
  storage:       0x94a3b8,
};

export function useWebGL(canvasRef: React.RefObject<HTMLCanvasElement>) {
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef    = useRef<THREE.Scene>(new THREE.Scene());
  const cameraRef   = useRef<THREE.OrthographicCamera | null>(null);
  const meshesRef   = useRef<Map<string, THREE.Mesh>>(new Map());

  const { components, edges } = useDesignStore();

  // Initialise renderer
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(canvas.clientWidth, canvas.clientHeight);
    rendererRef.current = renderer;

    const w = canvas.clientWidth, h = canvas.clientHeight;
    const camera = new THREE.OrthographicCamera(-w / 2, w / 2, h / 2, -h / 2, 0.1, 1000);
    camera.position.z = 10;
    cameraRef.current = camera;

    const scene = sceneRef.current;
    scene.background = new THREE.Color(0x0d0f1a);

    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
    };
  }, [canvasRef]);

  // Sync components to scene meshes
  useEffect(() => {
    const scene = sceneRef.current;
    const prevIds = new Set(meshesRef.current.keys());

    for (const comp of components) {
      prevIds.delete(comp.id);
      if (!meshesRef.current.has(comp.id)) {
        const geo = new THREE.BoxGeometry(60, 40, 1);
        const mat = new THREE.MeshBasicMaterial({
          color: COMPONENT_COLORS[comp.type] ?? 0xffffff,
          transparent: true,
          opacity: 0.85,
        });
        const mesh = new THREE.Mesh(geo, mat);
        scene.add(mesh);
        meshesRef.current.set(comp.id, mesh);
      }
      const mesh = meshesRef.current.get(comp.id)!;
      mesh.position.set(comp.x, comp.y, 0);
    }

    // Remove deleted
    for (const id of prevIds) {
      const mesh = meshesRef.current.get(id)!;
      scene.remove(mesh);
      meshesRef.current.delete(id);
    }
  }, [components]);

  return { scene: sceneRef, camera: cameraRef, renderer: rendererRef };
}
