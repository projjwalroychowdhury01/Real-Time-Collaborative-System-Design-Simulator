import { useEffect, useRef } from 'react';
import * as Y from 'yjs';
import { WebsocketProvider } from 'y-websocket';
import { useDesignStore } from '@/store/designStore';

const WS_BASE = (import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000').replace(/^http/, 'ws');

export function useCRDT(designId: number | null) {
  const docRef = useRef<Y.Doc | null>(null);

  useEffect(() => {
    if (!designId) return;

    const doc = new Y.Doc();
    docRef.current = doc;

    // Y.Map to hold the full design JSON
    const yComponents = doc.getArray<Y.Map<unknown>>('components');
    const yEdges = doc.getArray<Y.Map<unknown>>('edges');

    // Sync provider
    const provider = new WebsocketProvider(WS_BASE, `design-${designId}`, doc);

    // Observe remote changes and push to Zustand
    const observer = () => {
      const components = yComponents.toArray().map((m) => Object.fromEntries(m));
      const edges = yEdges.toArray().map((m) => Object.fromEntries(m));
      useDesignStore.setState({ components: components as any, edges: edges as any });
    };

    yComponents.observe(observer);
    yEdges.observe(observer);

    return () => {
      provider.destroy();
      doc.destroy();
    };
  }, [designId]);

  return { doc: docRef };
}
