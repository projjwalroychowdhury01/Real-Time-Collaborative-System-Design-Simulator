import { useRef } from 'react';
import { useWebGL } from '@/hooks/useWebGL';
import { useDesignStore } from '@/store/designStore';
import type { ComponentType } from '@/types/design';

export default function CanvasRenderer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useWebGL(canvasRef);

  const { addComponent } = useDesignStore();

  const handleDrop = (e: React.DragEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const type = e.dataTransfer.getData('component-type') as ComponentType;
    if (!type) return;
    const rect = (e.target as HTMLCanvasElement).getBoundingClientRect();
    addComponent({
      type,
      label: type.replace('_', ' '),
      x: e.clientX - rect.left - rect.width / 2,
      y: -(e.clientY - rect.top - rect.height / 2),
      replicas: 1,
      throughput: 1000,
      latency_ms: 10,
    });
  };

  return (
    <canvas
      ref={canvasRef}
      id="design-canvas"
      style={{ width: '100%', height: '100%', display: 'block' }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    />
  );
}
