"""Double-click launcher for Utah Flux Studio (no terminal window)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))

from utah_flux.studio import main  # noqa: E402

if __name__ == "__main__":
    main()
