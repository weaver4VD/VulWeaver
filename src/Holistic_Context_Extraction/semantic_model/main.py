"""
Standalone entry point to run semantic_model. Can be used with the same cache_dir
produced by VulWeaver or slice_antman, so that semantic_model can be run separately:

  python main.py --cache_dir /path/to/cache [--code_path /path/to/cache/code] [--language java]
  python -m Holistic_Context_Extraction.semantic_model.main --cache_dir /path/to/cache --language java
"""
import argparse
import os

import joern
from common import Language
from semantic_model import semantic_model, preprocess


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run semantic_model on a cache_dir (e.g. from VulWeaver/slice_antman)."
    )
    parser.add_argument(
        "--cache_dir",
        required=True,
        help="Cache directory (same as VulWeaver/slice_antman cache_path; must contain or will produce cpg, pdg, code).",
    )
    parser.add_argument(
        "--code_path",
        default=None,
        help="Path to code tree; default: <cache_dir>/code.",
    )
    parser.add_argument(
        "--joern_path",
        default=None,
        help="Joern install path; default: env JOERN_PATH.",
    )
    args = parser.parse_args()
    cache_dir = os.path.abspath(args.cache_dir)
    code_path = os.path.abspath(args.code_path) if args.code_path else os.path.join(cache_dir, "code")
    language = Language.JAVA
    joern_path = args.joern_path or os.environ.get("JOERN_PATH")
    if not joern_path:
        raise ValueError("Set JOERN_PATH env or pass --joern_path")
    return code_path, cache_dir, language, joern_path


def main(code_path: str, cache_dir: str, language: Language, joern_path: str) -> None:
    joern.set_joern_env(joern_path)
    os.makedirs(cache_dir, exist_ok=True)

    cpg = joern.export_with_preprocess_and_merge(
        code_path, cache_dir, language, False
    )

    call_node_info = preprocess(cache_dir)

    semantic_model(code_path, cache_dir, cpg, call_node_info)


if __name__ == "__main__":
    code_path, cache_dir, language, joern_path = _parse_args()
    main(code_path, cache_dir, language, joern_path)
