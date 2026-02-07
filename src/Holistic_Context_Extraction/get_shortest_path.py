import os, re
from typing import Iterable, List, Optional

def _normalize(p: str) -> str:
    p = re.sub(r"[\\/]+", "/", p.strip())
    return os.path.normpath(p).replace("\\", "/")

def _key(p: str, by: str):
    pn = _normalize(p)
    if by == "length":
        return (len(pn), pn)
    parts = [seg for seg in pn.split("/") if seg] or ["/"]
    return (len(parts), len(pn), pn)

def shortest_path_from_list(paths: Iterable[str], by: str = "components") -> Optional[str]:
    paths = [p for p in paths if p is not None and str(p).strip() != ""]
    if not paths:
        return None
    return min(paths, key=lambda p: _key(p, by))

def k_shortest_paths(paths: Iterable[str], by: str = "components", k: int = 3) -> List[str]:
    paths = [p for p in paths if p is not None and str(p).strip() != ""]
    paths.sort(key=lambda p: _key(p, by))
    return paths[:max(0, k)]