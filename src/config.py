import sys
import os
from pathlib import Path

# Detect if packed as EXE (PyInstaller/Nuitka sets sys.frozen)
# Pivot is a portable app, so we rely on the executable location in Prod
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # Prod: Directory containing the .exe file
    APP_ROOT = Path(sys.executable).parent
else:
    # Dev: Project root (parent of 'src'), pointing to 'dummy'
    # src/config.py -> src/ -> pivot/ -> dummy/
    APP_ROOT = Path(__file__).parent.parent / "dummy"

VERSIONS_DIR = APP_ROOT / "Versions"
PERSISTS_DIR = APP_ROOT / "Persists"

# Ensure directories exist (safe to run in both modes, though in prod user should provide them)
# We won't force create in prod to respect user intent, but for dev it's needed.
if not IS_FROZEN:
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)
    PERSISTS_DIR.mkdir(parents=True, exist_ok=True)
