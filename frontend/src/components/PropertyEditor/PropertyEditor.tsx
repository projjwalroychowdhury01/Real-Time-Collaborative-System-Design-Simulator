import { useDesignStore } from '@/store/designStore';

export default function PropertyEditor() {
  const { selectedId, components, updateComponent } = useDesignStore();
  const comp = components.find((c) => c.id === selectedId);

  if (!comp) {
    return (
      <aside className="prop-editor">
        <p className="hint">Select a component to edit its properties.</p>
      </aside>
    );
  }

  const update = (key: string, val: string | number) =>
    updateComponent(comp.id, { [key]: val });

  return (
    <aside className="prop-editor">
      <h3>{comp.label}</h3>
      <label>
        Label
        <input value={comp.label} onChange={(e) => update('label', e.target.value)} />
      </label>
      <label>
        Replicas
        <input type="number" min={1} value={comp.replicas} onChange={(e) => update('replicas', +e.target.value)} />
      </label>
      <label>
        Throughput (req/s)
        <input type="number" min={1} value={comp.throughput} onChange={(e) => update('throughput', +e.target.value)} />
      </label>
      <label>
        Latency (ms)
        <input type="number" min={0} value={comp.latency_ms} onChange={(e) => update('latency_ms', +e.target.value)} />
      </label>

      <style>{`
        .prop-editor { width: 220px; flex-shrink: 0; border-left: 1px solid var(--color-border); padding: var(--space-4); overflow-y: auto; }
        .prop-editor h3 { margin-bottom: var(--space-4); }
        .prop-editor label { display: flex; flex-direction: column; gap: var(--space-1); margin-bottom: var(--space-3); font-size: 0.8rem; color: var(--color-text-muted); }
        .prop-editor input { background: var(--color-surface-2); border: 1px solid var(--color-border); color: var(--color-text); padding: var(--space-2); border-radius: var(--radius-sm); font-family: var(--font-sans); font-size: 0.875rem; }
        .prop-editor input:focus { outline: none; border-color: var(--color-primary); }
        .hint { color: var(--color-text-muted); font-size: 0.8rem; }
      `}</style>
    </aside>
  );
}
