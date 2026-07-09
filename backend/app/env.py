from pathlib import Path

from dotenv import load_dotenv


def load_backend_env() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    load_dotenv(backend_root / ".env", override=False)
