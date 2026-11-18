"""Small, user-facing JSON file reading helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileHandlerError(Exception):
    """Raised when a JSON file cannot be read or decoded."""


def read_json_file(file_path: str | Path) -> Any:
    """Read and decode a UTF-8 JSON file with a helpful error message."""
    path = Path(file_path)
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileHandlerError(f"file not found: {path}") from None
    except PermissionError as exc:
        raise FileHandlerError(f"cannot read {path}: permission denied") from exc
    except UnicodeDecodeError as exc:
        raise FileHandlerError(f"{path} is not valid UTF-8 text") from exc
    except json.JSONDecodeError as exc:
        raise FileHandlerError(
            f"invalid JSON in {path} at line {exc.lineno}, column {exc.colno}"
        ) from None
    except OSError as exc:
        raise FileHandlerError(f"cannot read {path}: {exc}") from exc
