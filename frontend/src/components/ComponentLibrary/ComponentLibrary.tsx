import type { ComponentType } from '@/types/design';

const COMPONENTS: { type: ComponentType; label: string; icon: string }[] = [
  { type: 'api_gateway',   label: 'API Gateway',   icon: '🔀' },
  { type: 'microservice',  label: 'Microservice',  icon: '⚙️' },
  { type: 'database',      label: 'Database',      icon: '🗄️' },
  { type: 'cache',         label: 'Cache',         icon: '⚡' },
  { type: 'queue',         label: 'Message Queue', icon: '📨' },
  { type: 'load_balancer', label: 'Load Balancer', icon: '⚖️' },
  { type: 'cdn',           label: 'CDN',           icon: '🌐' },
  { type: 'storage',       label: 'Storage',       icon: '💾' },
];

export default function ComponentLibrary() {
  const onDragStart = (e: React.DragEvent, type: ComponentType) => {
    e.dataTransfer.setData('component-type', type);
  };

  return (
    <aside className="comp-library">
      <h3>Components</h3>
      <div className="comp-list">
        {COMPONENTS.map((c) => (
          <div
            key={c.type}
            className="comp-item"
            draggable
            id={`comp-${c.type}`}
            onDragStart={(e) => onDragStart(e, c.type)}
          >
            <span className="comp-icon">{c.icon}</span>
            <span>{c.label}</span>
          </div>
        ))}
      </div>

      <style>{`
        .comp-library { padding: var(--space-4); border-right: 1px solid var(--color-border); width: 180px; flex-shrink: 0; overflow-y: auto; }
        .comp-library h3 { margin-bottom: var(--space-3); color: var(--color-text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; }
        .comp-list { display: flex; flex-direction: column; gap: var(--space-2); }
        .comp-item { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-2) var(--space-3); border-radius: var(--radius-sm); border: 1px solid var(--color-border); background: var(--color-surface-2); cursor: grab; font-size: 0.8rem; transition: border-color 0.15s, transform 0.1s; user-select: none; }
        .comp-item:hover { border-color: var(--color-primary); transform: translateX(2px); }
        .comp-item:active { cursor: grabbing; }
        .comp-icon { font-size: 1rem; }
      `}</style>
    </aside>
  );
}
