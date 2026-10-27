from pathlib import Path
import os

def _find_root() -> Path:
    if env := os.getenv("EMM_ROOT"):
        return Path(env).resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not find project root. Please set the EMM_ROOT environment variable.")

ROOT_PATH = _find_root()
DATA_PATH = ROOT_PATH.joinpath("data")
CONFIG_PATH = ROOT_PATH.joinpath("configs")