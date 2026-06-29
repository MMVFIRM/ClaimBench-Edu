from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


def load_data(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("YAML support requires pyyaml. Install with `pip install pyyaml`.")
        data = yaml.safe_load(text)
    elif suffix == ".json":
        data = json.loads(text)
    else:
        raise ValueError(f"Unsupported package format: {p.suffix}. Use .yaml, .yml, or .json")
    if not isinstance(data, dict):
        raise ValueError("Data must load to an object/dict.")
    return data


def load_claim_package(path: str | Path) -> Dict[str, Any]:
    data = load_data(path)
    # Signed package envelopes are explicit containers; evaluation uses the package payload.
    if data.get("schema") in {"claimbench.signed_package.v2.0", "claimbench.signed_package.v2.1"} and "package" in data:
        pkg = data["package"]
        if not isinstance(pkg, dict):
            raise ValueError("Signed package envelope contains a non-object package payload.")
        return pkg
    return data


def write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=False), encoding="utf-8")


def write_yaml(path: str | Path, data: Dict[str, Any]) -> None:
    if yaml is None:
        raise RuntimeError("YAML support requires pyyaml. Install with `pip install pyyaml`.")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def write_data(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    if p.suffix.lower() in {".yaml", ".yml"}:
        write_yaml(p, data)
    elif p.suffix.lower() == ".json":
        write_json(p, data)
    else:
        raise ValueError(f"Unsupported output format: {p.suffix}. Use .yaml, .yml, or .json")


def write_text(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
