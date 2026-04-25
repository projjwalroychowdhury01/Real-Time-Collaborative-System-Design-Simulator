"""
Phase 1 — Developer Quick-Start Script.

Usage (from the `backend/` directory):
    python scripts/quickstart.py

This script verifies the local environment is correctly configured for
Phase 1 development before starting Docker Compose:
  1. Check Python version (≥3.11)
  2. Check required packages are importable
  3. Validate .env file exists and DATABASE_URL uses asyncpg driver
  4. Print next steps
"""
import sys
import subprocess


def check_python():
    major, minor = sys.version_info[:2]
    if major < 3 or minor < 11:
        print(f"❌  Python 3.11+ required. Found: {major}.{minor}")
        sys.exit(1)
    print(f"✅  Python {major}.{minor}")


def check_packages():
    required = [
        "fastapi", "uvicorn", "sqlalchemy", "asyncpg",
        "authlib", "jose", "pydantic_settings", "alembic",
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✅  {pkg}")
        except ImportError:
            print(f"❌  {pkg} — not installed")
            missing.append(pkg)

    if missing:
        print(f"\n🔧  Install missing packages with:")
        print(f"    pip install -r requirements.txt")
        sys.exit(1)


def check_env():
    from pathlib import Path
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("❌  backend/.env file not found. Copy .env.example → .env and fill in values.")
        sys.exit(1)
    content = env_path.read_text()
    if "+asyncpg" not in content:
        print("❌  DATABASE_URL in .env must use 'postgresql+asyncpg://' scheme.")
        sys.exit(1)
    print("✅  .env file found with asyncpg driver")


def print_next_steps():
    print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Phase 1 — Ready to start!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 1. Start infrastructure:
      docker-compose up -d db redis

 2. Run migrations:
      python -m alembic upgrade head

 3. Start API server:
      uvicorn app.main:app --reload

 4. Open API docs:
      http://localhost:8000/docs

 5. Run Phase 1 tests:
      pytest tests/test_phase1.py -v

 6. OAuth setup:
      - Google: https://console.cloud.google.com/apis/credentials
      - GitHub:  https://github.com/settings/developers
      Fill GOOGLE_CLIENT_* and GITHUB_CLIENT_* in backend/.env
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    print("\n🔍  Phase 1 Environment Check\n")
    check_python()
    check_packages()
    check_env()
    print_next_steps()
