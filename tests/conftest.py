from pathlib import Path
import sys

SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent / "src"
if str(SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SOURCE_DIRECTORY))
