"""geometry.json(단일 출처)을 중첩 SimpleNamespace로 로드. 값은 전부 여기서만 온다."""
import json
import types


def _ns(d):
    return types.SimpleNamespace(
        **{k: (_ns(v) if isinstance(v, dict) else v) for k, v in d.items()}
    )


def load_config(path="geometry.json"):
    with open(path, encoding="utf-8") as f:
        return _ns(json.load(f))
