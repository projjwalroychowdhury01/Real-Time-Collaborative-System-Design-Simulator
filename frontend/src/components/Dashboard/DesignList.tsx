import { useEffect, useState } from 'react';
import api from '@/utils/api';
import type { Design } from '@/types/design';

export default function DesignList() {
  const [designs, setDesigns] = useState<Design[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/designs')
      .then((r) => setDesigns(r.data))
      .finally(() => setLoading(false));
  }, []);

  const createDesign = async () => {
    const name = prompt('Design name:');
    if (!name) return;
    const { data } = await api.post('/designs', { name });
    setDesigns((prev) => [data, ...prev]);
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>My Designs</h1>
        <button className="btn btn-primary" id="create-design-btn" onClick={createDesign}>
          + New Design
        </button>
      </header>

      {loading ? (
        <p className="muted">Loading…</p>
      ) : designs.length === 0 ? (
        <p className="muted">No designs yet. Create your first one!</p>
      ) : (
        <div className="design-grid">
          {designs.map((d) => (
            <a key={d.id} className="card design-card" href={`/editor/${d.id}`}>
              <h3>{d.name}</h3>
              <p>{d.description || 'No description'}</p>
              <small>{new Date(d.updated_at).toLocaleDateString()}</small>
            </a>
          ))}
        </div>
      )}

      <style>{`
        .dashboard { padding: var(--space-8); max-width: 1100px; margin: 0 auto; }
        .dashboard-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: var(--space-6); }
        .design-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: var(--space-4); }
        .design-card { display: block; text-decoration: none; color: inherit; transition: border-color 0.2s, transform 0.15s; }
        .design-card:hover { border-color: var(--color-primary); transform: translateY(-2px); }
        .design-card h3 { margin-bottom: var(--space-1); }
        .design-card small { color: var(--color-text-muted); font-size: 0.75rem; }
        .muted { color: var(--color-text-muted); margin-top: var(--space-6); }
      `}</style>
    </div>
  );
}
