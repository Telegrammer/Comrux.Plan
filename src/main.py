from pathlib import Path
import sys

SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def build_app():
    from app_factory import create_app

    return create_app()


app = build_app()

if __name__ == "__main__":
    import uvicorn
    from setup.config import settings

    uvicorn.run(app, host=settings.run.host, port=settings.run.port, reload=False)
