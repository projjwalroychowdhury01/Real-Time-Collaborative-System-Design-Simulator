import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuthStore } from '@/store/uiStore';

/**
 * OAuth callback page.
 * Extracts the JWT token from the `?token=` query param and stores it.
 */
export default function OAuthCallback() {
  const [params] = useSearchParams();
  const setToken = useAuthStore((s) => s.setToken);
  const navigate = useNavigate();

  useEffect(() => {
    const token = params.get('token');
    if (token) {
      setToken(token);
      navigate('/', { replace: true });
    } else {
      navigate('/login', { replace: true });
    }
  }, [params, setToken, navigate]);

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
      <p style={{ color: 'var(--color-text-muted)' }}>Signing you in…</p>
    </div>
  );
}
