"""
Shared I/O utilities for APSCA scripts.
"""

import json
from pathlib import Path
from typing import List, Dict, Any


def load_json(file_path: Path) -> List[Dict]:
    """Load JSON array from file. Returns empty list if file is empty or missing."""
    if not file_path.exists():
        return []
    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return json.loads(content)


def save_json(file_path: Path, data: Any, indent: int = 2) -> None:
    """Save data as JSON to file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
        f.write('\n')
