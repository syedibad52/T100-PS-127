import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from allocation_engine.cli import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # A report may intentionally be piped to a short preview command.
        raise SystemExit(0)
