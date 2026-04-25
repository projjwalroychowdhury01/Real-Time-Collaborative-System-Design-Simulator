import { useEffect, useState } from 'react';
import api from '@/utils/api';
import { useDesignStore } from '@/store/designStore';
import { formatDistanceToNow } from 'date-fns';

interface Checkpoint {
  id: number;
  checkpoint_number: number;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export default function CheckpointTimeline() {
  const designId = useDesignStore((s) => s.designId);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const { setDesign } = useDesignStore();

  useEffect(() => {
    if (!designId) return;
    api.get(`/designs/${designId}/checkpoints`).then((r) => setCheckpoints(r.data));
  }, [designId]);

  const loadCheckpoint = async (cpId: number) => {
    if (!designId) return;
    const { data } = await api.get(`/designs/${designId}/checkpoints/${cpId}`);
    setDesign(designId, data.design_json);
  };

  return (
    <div className="checkpoint-timeline">
      <h3>Checkpoints</h3>
      {checkpoints.length === 0 ? (
        <p className="muted-sm">Auto-saves appear here every minute.</p>
      ) : (
        <ul className="cp-list">
          {checkpoints.map((cp) => (
            <li key={cp.id} className="cp-item" onClick={() => loadCheckpoint(cp.id)}>
              <span className="cp-num">#{cp.checkpoint_number}</span>
              <span className="cp-time">{formatDistanceToNow(new Date(cp.created_at), { addSuffix: true })}</span>
            </li>
          ))}
        </ul>
      )}

      <style>{`
        .checkpoint-timeline { padding: var(--space-4); }
        .checkpoint-timeline h3 { margin-bottom: var(--space-3); font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--color-text-muted); }
        .cp-list { list-style: none; display: flex; flex-direction: column; gap: var(--space-2); }
        .cp-item { display: flex; justify-content: space-between; align-items: center; padding: var(--space-2) var(--space-3); background: var(--color-surface-2); border: 1px solid var(--color-border); border-radius: var(--radius-sm); cursor: pointer; font-size: 0.8rem; transition: border-color 0.15s; }
        .cp-item:hover { border-color: var(--color-primary); }
        .cp-num { color: var(--color-accent); font-weight: 600; }
        .cp-time { color: var(--color-text-muted); }
        .muted-sm { color: var(--color-text-muted); font-size: 0.8rem; }
      `}</style>
    </div>
  );
}
