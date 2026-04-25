const API_BASE = '/api';

export default function LoginPage() {
  return (
    <div className="login-page">
      <div className="login-card card">
        <h1>System Design Simulator</h1>
        <p>Practice distributed systems design collaboratively in real-time.</p>
        <div className="login-buttons">
          <a href={`${API_BASE}/auth/login/google`} className="btn btn-primary" id="login-google">
            Sign in with Google
          </a>
          <a href={`${API_BASE}/auth/login/github`} className="btn btn-ghost" id="login-github">
            Sign in with GitHub
          </a>
        </div>
      </div>

      <style>{`
        .login-page {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          background: radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.15) 0%, transparent 70%),
                      var(--color-bg);
        }
        .login-card {
          width: 360px;
          text-align: center;
          padding: var(--space-8);
          box-shadow: var(--shadow-md), var(--shadow-glow);
        }
        .login-card h1 { margin-bottom: var(--space-2); font-size: 1.4rem; }
        .login-card p  { margin-bottom: var(--space-6); }
        .login-buttons { display: flex; flex-direction: column; gap: var(--space-3); }
        .login-buttons .btn { justify-content: center; }
      `}</style>
    </div>
  );
}
