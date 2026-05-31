#!/usr/bin/env python3
"""Odysseus — first-time setup script.

Creates data directories, initializes the database, and sets up an
initial admin user. Safe to re-run (skips what already exists).
"""

import os
import platform
import shutil
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

DIRS = [
    DATA_DIR,
    os.path.join(DATA_DIR, "uploads"),
    os.path.join(DATA_DIR, "personal_docs"),
    os.path.join(DATA_DIR, "personal_uploads"),
    os.path.join(DATA_DIR, "tts_cache"),
    os.path.join(DATA_DIR, "generated_images"),
    os.path.join(DATA_DIR, "deep_research"),
    os.path.join(DATA_DIR, "chroma"),
    os.path.join(DATA_DIR, "rag"),
    os.path.join(DATA_DIR, "memory_vectors"),
    os.path.join(BASE_DIR, "logs"),
]


def create_dirs():
    for d in DIRS:
        os.makedirs(d, exist_ok=True)
        print(f"  [ok] {os.path.relpath(d, BASE_DIR)}/")


def init_database():
    """Create all SQLAlchemy tables."""
    sys.path.insert(0, BASE_DIR)
    os.environ.setdefault("DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'app.db')}")

    from core.database import Base, engine
    Base.metadata.create_all(bind=engine)
    print("  [ok] Database initialized")


def create_default_admin():
    """Create an initial admin user if none exists."""
    if os.getenv("ODYSSEUS_SKIP_ADMIN_CREATE", "").lower() in {"1", "true", "yes"}:
        print("  [skip] admin creation disabled by ODYSSEUS_SKIP_ADMIN_CREATE")
        return

    auth_path = os.path.join(DATA_DIR, "auth.json")
    if os.path.exists(auth_path):
        print("  [skip] auth.json already exists")
        return

    try:
        import bcrypt
        import json

        username = os.getenv("ODYSSEUS_ADMIN_USER", "admin").strip() or "admin"
        password = os.getenv("ODYSSEUS_ADMIN_PASSWORD") or __import__("secrets").token_urlsafe(18)
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        auth_data = {
            "users": {
                username: {
                    "password_hash": hashed,
                    "is_admin": True,
                }
            }
        }
        with open(auth_path, "w") as f:
            json.dump(auth_data, f, indent=2)
        print(f"  [ok] Initial admin user created ({username})")
        print(f"        Temporary password: {password}")
        print(f"        ** Change it after first login. Set ODYSSEUS_ADMIN_PASSWORD to choose your own. **")
    except ImportError:
        print("  [warn] bcrypt not installed — skipping admin user creation")
        print("         Run: pip install bcrypt")


def auth_has_users():
    """Return True when a local auth file already contains at least one user."""
    auth_path = os.path.join(DATA_DIR, "auth.json")
    try:
        with open(auth_path) as f:
            data = json.load(f)
    except Exception:
        return False
    return bool(data.get("users"))


def create_env():
    """Copy .env.example to .env if it doesn't exist."""
    env_path = os.path.join(BASE_DIR, ".env")
    example_path = os.path.join(BASE_DIR, ".env.example")
    if os.path.exists(env_path):
        print("  [skip] .env already exists")
        return
    if os.path.exists(example_path):
        import shutil
        shutil.copy2(example_path, env_path)
        print("  [ok] .env created from .env.example")
        print("        ** Edit .env with your LLM host and API keys **")
    else:
        print("  [warn] .env.example not found — create .env manually")


def check_python():
    """Warn early when the active interpreter is too old."""
    if sys.version_info < (3, 11):
        print(f"  [warn] Python {sys.version.split()[0]} detected; Odysseus needs Python 3.11+")
        if platform.system() == "Darwin":
            print("         On macOS: brew install python@3.13")
        else:
            print("         Install Python 3.11+ with your OS package manager or pyenv.")
    else:
        print(f"  [ok] Python {sys.version.split()[0]}")


def check_deps():
    """Check for common missing dependencies."""
    missing = []
    for mod in ["fastapi", "uvicorn", "sqlalchemy", "bcrypt", "httpx", "dotenv"]:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
    if missing:
        print(f"\n  [warn] Missing packages: {', '.join(missing)}")
        print(f"         Run: pip install -r requirements.txt")
    else:
        print("  [ok] All core dependencies installed")

    if os.name != "nt" and shutil.which("tmux") is None:
        print("\n  [warn] tmux not found")
        print("         Cookbook uses tmux for background downloads and model serves.")
        print("         Install it with your OS package manager, for example:")
        if platform.system() == "Darwin":
            print("           brew install tmux")
        else:
            print("           sudo apt install tmux")
            print("           sudo pacman -S tmux")
            print("           sudo dnf install tmux")
    elif os.name != "nt":
        print("  [ok] tmux installed")


def main():
    print("\n=== Odysseus Setup ===\n")

    print("1. Creating directories...")
    create_dirs()

    print("\n2. Environment file...")
    create_env()

    print("\n3. Checking Python...")
    check_python()

    print("\n4. Checking dependencies...")
    check_deps()

    print("\n5. Initializing database...")
    try:
        init_database()
    except Exception as e:
        print(f"  [warn] Database init failed: {e}")
        print("         This is OK if dependencies aren't installed yet.")

    print("\n6. Creating initial admin...")
    try:
        create_default_admin()
    except Exception as e:
        print(f"  [warn] Admin creation failed: {e}")

    print("\n=== Setup complete ===")
    default_port = "7001" if platform.system() == "Darwin" else "7000"
    port = os.getenv("ODYSSEUS_PORT", default_port)
    base_url = os.getenv("ODYSSEUS_INTERNAL_BASE_URL", f"http://127.0.0.1:{port}")
    print("\nStart the server with:")
    print(f"  ODYSSEUS_PORT={port} ODYSSEUS_INTERNAL_BASE_URL={base_url} \\")
    print(f"    uvicorn app:app --host 127.0.0.1 --port {port}")
    print(f"\nThen open {base_url}")
    if auth_has_users():
        print("Login with your existing admin account.\n")
    elif os.getenv("ODYSSEUS_SKIP_ADMIN_CREATE", "").lower() in {"1", "true", "yes"}:
        print("On first start, Odysseus will print a local setup URL with a one-time token.\n")
    else:
        print("Login with the admin username and temporary password printed above.\n")


if __name__ == "__main__":
    main()
