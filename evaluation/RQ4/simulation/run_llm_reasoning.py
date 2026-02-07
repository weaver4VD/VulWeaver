from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from prompt import prompt_snippet_templates
from prompt.vulnerability_guidelines.vulnerability_constants import (
    CWE_GUIDELINE_MAP,
    CWE_NAME_MAP,
)

@dataclass(frozen=True)
class OutputPaths:
    output_dir: Path
    run_id: str
    language: str

    @property
    def results_path(self) -> Path:
        return self.output_dir / f"reasoning_results_{self.language}_{self.run_id}.json"

    @property
    def vulnerabilities_path(self) -> Path:
        return self.output_dir / f"reasoning_vulnerabilities_{self.language}_{self.run_id}.json"

    @property
    def artifacts_path(self) -> Path:
        return self.output_dir / f"reasoning_artifacts_{self.language}_{self.run_id}.json"


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: Path, obj: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

class DeepSeekAPI:
    """DeepSeek API client."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.deepseek.com"):
        """
        Initialize the DeepSeek API client.
        
        Args:
            api_key: API key. If None, read from env var DEEPSEEK_API_KEY.
            base_url: API base URL.
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("Missing API key. Set DEEPSEEK_API_KEY or pass --api-key.")
        
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        timeout_s: int,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response = self.session.post(url, json=payload, timeout=timeout_s)
        response.raise_for_status()
        return response.json()


def _normalize_bool(v: Any) -> Optional[bool]:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in {"true", "yes", "y", "1"}:
            return True
        if s in {"false", "no", "n", "0"}:
            return False
    return None


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def extract_first_json_object(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).replace("```", "").strip()
    decoder = json.JSONDecoder()
    for i, ch in enumerate(cleaned):
        if ch != "{":
            continue
        try:
            obj, _end = decoder.raw_decode(cleaned[i:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


def vote_result(round_results: List[Dict]) -> Dict:
    if not round_results:
        return None

    def get_score(res: Dict[str, Any]) -> float:
        return _safe_float(res.get("confidence_score", 0), 0.0)

    max_score = -1.0
    if round_results:
        max_score = max(get_score(r) for r in round_results)

    best_results = [r for r in round_results if get_score(r) == max_score]
    
    if len(best_results) == 1:
        final_result = best_results[0].copy()
        final_result['vote_stats'] = {
            'total_rounds': len(round_results),
            'max_score_candidates': 1,
            'selected_confidence': max_score,
            'strategy': 'single_max_confidence'
        }
        return final_result

    vulnerable_votes = sum(1 for r in best_results if _normalize_bool(r.get("is_vulnerable")) is True)
    safe_votes = len(best_results) - vulnerable_votes

    final_is_vulnerable = vulnerable_votes > safe_votes

    base_result = next(
        (r for r in best_results if _normalize_bool(r.get("is_vulnerable")) == final_is_vulnerable),
        best_results[0],
    )
    
    final_result = base_result.copy()
    final_result["is_vulnerable"] = final_is_vulnerable

    final_result["vote_stats"] = {
        "total_rounds": len(round_results),
        "max_score_candidates": len(best_results),
        "vulnerable_votes_in_best": vulnerable_votes,
        "safe_votes_in_best": safe_votes,
        "selected_confidence": max_score,
        "consensus": vulnerable_votes == len(best_results) or safe_votes == len(best_results),
        "strategy": "vote_among_max_confidence",
    }
    
    return final_result


def extract_imports(code: str, language: str) -> List[str]:
    if language == "java":
        try:
            from src.Constructing_Enhanced_UDG import common
            from src.Constructing_Enhanced_UDG.ast_parser import ASTParser
            imports: set[str] = set()
            ast_parser = ASTParser(code, common.Language.JAVA)
            for node in ast_parser.get_all_includes():
                raw = node.text
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8")
                imports.add(raw.strip())
            return sorted(imports)
        except Exception:
            imports = []
            for line in code.splitlines():
                s = line.strip()
                if "import " in s and s.endswith(";"):
                    imports.append(s)
            return sorted(set(imports))
    elif language == "c":
        include_pattern = re.compile(r'#\s*include\s*[<"]([^>"]+)[>"]')
        return sorted(set(include_pattern.findall(code)))
    return []


def _read_code_bundle(method_signature_dir: Path, language: str) -> Tuple[str, List[str], Optional[str]]:
    """
    Read code snippet(s) from cache_dir layout: method/<method_signature>/target_slicing_code.{lang}.
    For each subdir under method/, prefers target_slicing_code.{language}; falls back to target.{language}.
    Returns (combined_code, imports, error_message).
    """
    method_dir = method_signature_dir / "method"
    if not method_dir.exists():
        return "", [], f"Missing directory: {method_dir}"

    combined = []
    all_imports: List[str] = []
    for child in sorted(method_dir.iterdir()):
        if not child.is_dir():
            continue
        slicing = child / f"target_slicing_code.{language}"
        raw = child / f"target.{language}"
        file_to_read = slicing if slicing.exists() else (raw if raw.exists() else None)
        if not file_to_read:
            continue
        try:
            code = file_to_read.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        print(code)
        print("!!!!!!!!!!!!!!!")
        all_imports.extend(extract_imports(code, language))
        combined.append(f"// Method: {child.name}\n{code}\n")

    if not combined:
        return "", sorted(set(all_imports)), "No readable target code snippets found"
    return "\n".join(combined).strip() + "\n", sorted(set(all_imports)), None


def _build_prompts(
    language: str,
    cwe: str,
    method_signature: str,
    sensitive_api: str,
    code_snippet: str,
    imports: List[str],
) -> List[Dict[str, str]]:
    cwe_name = CWE_NAME_MAP.get(cwe, cwe)
    cwe_guideline = CWE_GUIDELINE_MAP.get(cwe, "No guideline available")

    if language == "java":
        system_prompt = prompt_snippet_templates.SYSTEM_PROMPT_TEMPLATE_JAVA.format(vulnerability_type=cwe_name)
        if imports:
            user_prompt = prompt_snippet_templates.USER_PROMPT_TEMPLATE_WITH_IMPORTS_JAVA.format(
                cwe_guideline=cwe_guideline,
                imports=", ".join(imports),
                vulnerability_type=cwe_name,
                target_function_name=method_signature,
                sensitive_api=sensitive_api,
                code_snippet=code_snippet,
            )
        else:
            user_prompt = prompt_snippet_templates.USER_PROMPT_TEMPLATE_JAVA.format(
                cwe_guideline=cwe_guideline,
                vulnerability_type=cwe_name,
                target_function_name=method_signature,
                sensitive_api=sensitive_api,
                code_snippet=code_snippet,
            )
    else:
        system_prompt = prompt_snippet_templates.SYSTEM_PROMPT_TEMPLATE_C_CPP.format(vulnerability_type=cwe_name)
        user_prompt = prompt_snippet_templates.USER_PROMPT_TEMPLATE_C_CPP.format(
            cwe_guideline=cwe_guideline,
            vulnerability_type=cwe_name,
            target_function_name=method_signature,
            sensitive_api=sensitive_api,
            code_snippet=code_snippet,
        )

    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
_PRIMEVUL_TEST_PATH = (
    Path(__file__).resolve().parent / ".." / "primevul_dataset" / "primevul_test_formatted.json"
).resolve()


@dataclass(frozen=True)
class ReasoningTask:
    repo_name: str
    method_signature: str
    method_signature_dir: Path
    cwe: str
    api: str

    def key(self, legacy_key: bool) -> str:
        if legacy_key:
            return f"{self.method_signature_dir}#{self.method_signature}#{self.cwe}#{self.api}"
        return f"{self.repo_name}#{self.method_signature}#{self.cwe}#{self.api}"


def iter_reasoning_tasks_from_primevul_and_cache(
    primevul_path: Path,
    cache_dir: Path,
) -> Iterable[ReasoningTask]:
    """
    Yield reasoning tasks from primevul_test_formatted.json entries that have an existing
    cache under cache_dir. Each task reads code from cache_dir/cache_<key>/method/
    (same layout as run_simulation_primevul / detect_primevul). Result key format
    matches detect_primevul: {cache_path}#{method_signature}#{cwe}#{api}.
    """
    data = _load_json(primevul_path, default=[])
    if not isinstance(data, list):
        return
    for row in data:
        if not isinstance(row, dict):
            continue
        target_method = row.get("target_method")
        if not target_method or (target_method or "").strip().endswith("#") or "#" not in (target_method or ""):
            continue
        project_url = (row.get("project_url") or "").strip()
        project_name = project_url.split("/")[-1].replace(".git", "") if project_url else ""
        file_path = target_method.strip().split("#")[0]
        file_name = file_path.split("/")[-1] if "/" in file_path else file_path
        method_name = target_method.strip().split("#")[-1]
        idx = str(row.get("idx", ""))
        cve_id = str(row.get("CVE_id", ""))
        commit_id = str(row.get("commit_id", ""))
        is_vul = bool(row.get("is_vulnerable", False))
        label = "vulnerable" if is_vul else "fixed"
        cwe = str(row.get("CWE_id", ""))
        target_api_name = row.get("target_api_name")
        if not isinstance(target_api_name, list):
            target_api_name = []
        api_str = ",".join(target_api_name)

        cache_key = f"{project_name}#{file_name}#{method_name}#{idx}#{cve_id}#{commit_id}#{label}"
        cache_path = cache_dir / f"cache_{cache_key}"
        if not cache_path.exists():
            continue

        yield ReasoningTask(
            repo_name=project_name,
            method_signature=method_name,
            method_signature_dir=cache_path,
            cwe=cwe,
            api=api_str,
        )


def run_reasoning_for_task(
    task: ReasoningTask,
    api_key: str,
    base_url: str,
    language: str,
    model: str,
    temperature: float,
    max_tokens: Optional[int],
    rounds: int,
    start_round: int,
    timeout_s: int,
    sleep_on_error_s: float,
    legacy_key: bool,
    save_artifacts: bool,
) -> Tuple[str, Optional[List[Dict[str, Any]]], Optional[str], Optional[Dict[str, Any]]]:
    """
    Returns: (key, round_results, error_message, optional_artifacts)
    """
    key = task.key(legacy_key=legacy_key)
    code_snippet, imports, read_err = _read_code_bundle(task.method_signature_dir, language)
    if read_err:
        return key, None, read_err, None

    messages = _build_prompts(language, task.cwe, task.method_signature, task.api, code_snippet, imports)
    client = DeepSeekAPI(api_key=api_key, base_url=base_url)

    round_results: List[Dict[str, Any]] = []
    attempts = 0
    max_attempts = max(1, rounds * 2)
    while len(round_results) < rounds and attempts < max_attempts:
        attempts += 1
        try:
            response = client.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
            )
            choices = response.get("choices") or []
            if not choices:
                time.sleep(sleep_on_error_s)
                continue
            content = choices[0].get("message", {}).get("content", "")
            parsed = extract_first_json_object(content)
            if not parsed:
                time.sleep(sleep_on_error_s)
                continue
            parsed["round"] = start_round + len(round_results) + 1
            round_results.append(parsed)
        except Exception:
            time.sleep(sleep_on_error_s)
            continue

    if not round_results:
        return key, None, f"No successful rounds after {attempts} attempts", None

    artifacts = None
    if save_artifacts:
        artifacts = {
            "code_snippet": code_snippet,
            "imports": imports,
            "messages": messages,
        }
    return key, round_results, None, artifacts

def _reverse_cwe_api_map(sensitive_api_mapping: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Input: { cwe: [api1, api2, ...] }
    Output: { api: [cwe1, cwe2, ...] }
    """
    api_to_cwes: Dict[str, List[str]] = {}
    for cwe, apis in (sensitive_api_mapping or {}).items():
        if not isinstance(apis, list):
            continue
        for api in apis:
            if api not in api_to_cwes:
                api_to_cwes[api] = []
            api_to_cwes[api].append(cwe)
    return api_to_cwes


def load_sensitive_api_mapping_for_lang(path: Path, lang: str) -> Dict[str, List[str]]:
    """
    Load sensitive API mapping for a language.

    Supported formats:
    1) Single-language: { "CWE-xx": ["api1", ...], ... }
    2) Merged-by-language: { "java": {...}, "c": {...} }

    Returns a mapping shaped as: { cwe: [api...] }.
    """
    raw = _load_json(path, default={})
    if not isinstance(raw, dict):
        raise ValueError("Invalid sensitive API JSON: expected an object")
    if any(k in raw for k in ("java", "c", "cpp", "c_cpp")):
        key_candidates = [lang]
        if lang == "c":
            key_candidates += ["c_cpp", "cpp"]
        selected = None
        for k in key_candidates:
            v = raw.get(k)
            if isinstance(v, dict):
                selected = v
                break
        if selected is None:
            raise ValueError(f"No mapping found for language '{lang}' in merged file")
        raw = selected
    mapping: Dict[str, List[str]] = {}
    for cwe, apis in raw.items():
        if not isinstance(cwe, str):
            continue
        if isinstance(apis, list):
            mapping[cwe] = [a for a in apis if isinstance(a, str)]
        else:
            mapping[cwe] = []
    return mapping


def iter_reasoning_tasks(cache_dir: Path, api_to_cwes: Dict[str, List[str]]) -> Iterable[ReasoningTask]:
    """
    Yields reasoning tasks from cache_dir. Supports two layouts:
    1. Flat (VulWeaver): cache_dir has sensitive_api.json and method/ directly.
    2. Nested: cache_dir contains repo subdirs, each with sensitive_api.json and method/.
    """
    def _collect_repos() -> Iterable[Tuple[Path, str]]:
        repo_sensitive_api = cache_dir / "sensitive_api.json"
        method_base = cache_dir / "method"
        if repo_sensitive_api.exists() and method_base.exists():
            yield cache_dir, cache_dir.name
            return
        for repo in sorted(cache_dir.iterdir()):
            if not repo.is_dir():
                continue
            repo_sensitive_api = repo / "sensitive_api.json"
            method_base = repo / "method"
            if not repo_sensitive_api.exists() or not method_base.exists():
                continue
            yield repo, repo.name

    for repo_path, repo_name in _collect_repos():
        repo_sensitive_api = repo_path / "sensitive_api.json"
        method_base = repo_path / "method"

        api_method_mapping = _load_json(repo_sensitive_api, default={})
        if not isinstance(api_method_mapping, dict):
            continue

        method_sig_to_api_and_cwes: Dict[str, Tuple[str, List[str]]] = {}
        for api, methods in api_method_mapping.items():
            if api not in api_to_cwes:
                continue
            if not isinstance(methods, list):
                continue
            for m in methods:
                if not isinstance(m, str):
                    continue
                clean_sig = "#".join(m.replace("/", ".").split("#")[:-1])
                if clean_sig not in method_sig_to_api_and_cwes:
                    method_sig_to_api_and_cwes[clean_sig] = (api, api_to_cwes.get(api, []))

        for method_signature_dir in sorted(method_base.iterdir()):
            if not method_signature_dir.is_dir():
                continue
            method_signature = method_signature_dir.name
            if method_signature not in method_sig_to_api_and_cwes:
                continue
            api, cwes = method_sig_to_api_and_cwes[method_signature]
            for cwe in cwes:
                yield ReasoningTask(
                    repo_name=repo_name,
                    method_signature=method_signature,
                    method_signature_dir=method_signature_dir,
                    cwe=cwe,
                    api=api,
                )


def build_vulnerabilities_summary(
    results: Dict[str, Any],
    artifacts: Dict[str, Any],
    include_code: bool,
) -> Dict[str, Any]:
    """
    Generate a compact summary file:
    - vote among rounds
    - keep only is_vulnerable == True
    """
    summary: Dict[str, Any] = {}
    for key, rounds in (results or {}).items():
        if not isinstance(rounds, list) or not rounds:
            continue
        voted = vote_result(rounds)
        if not voted:
            continue
        if _normalize_bool(voted.get("is_vulnerable")) is not True:
            continue

        explanations = []
        for r in rounds:
            exp = r.get("explanation")
            if isinstance(exp, str) and exp.strip():
                explanations.append(exp)

        item = {
            "is_vulnerable": True,
            "confidence_score": voted.get("confidence_score"),
            "vote_stats": voted.get("vote_stats", {}),
            "explanations": explanations,
        }
        if include_code:
            item["code_snippet"] = (artifacts.get(key) or {}).get("code_snippet")
        summary[key] = item
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Vulnerability Reasoning Pipeline (LLM-based)")
    parser.add_argument("--lang", choices=["java", "c", "c++", "cpp", "cxx"], default="java", help="Programming language")
    parser.add_argument("--cache-dir", required=True, help="Base cache directory under which cache_<key> dirs exist (e.g. effectiveness_evaluation_context)")
    parser.add_argument(
        "--primevul-worklist",
        type=Path,
        default=None,
        help="Path to primevul_test_formatted.json; if set and file exists, tasks are built from its entries and only run for existing cache_dir/cache_<key> dirs (default: ../primevul_dataset/primevul_test_formatted.json)",
    )
    parser.add_argument(
        "--sensitive-api-map",
        default=str(Path(__file__).resolve().parent / "sensitive_api" / "sensitive_api.json"),
        help="Sensitive API mapping JSON (single-language or merged-by-lang).",
    )
    parser.add_argument("--output-dir", default="./outputs", help="Output directory (default: ./outputs)")
    parser.add_argument("--run-id", default="default", help="Run identifier used in output filenames")

    parser.add_argument("--rounds", type=int, default=1, help="Reasoning rounds per item")
    parser.add_argument("--workers", type=int, default=32, help="Max parallel workers (threads)")
    parser.add_argument("--resume", action="store_true", help="Resume from existing results file")
    parser.add_argument(
        "--legacy-key",
        action="store_true",
        help="Use legacy key format based on absolute method directory path",
    )

    parser.add_argument("--model", default="deepseek-reasoner", help="Model name")
    parser.add_argument("--base-url", default="https://api.deepseek.com", help="DeepSeek API base URL")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, default=None, help="Max tokens (optional)")
    parser.add_argument("--timeout-s", type=int, default=60, help="Request timeout (seconds)")
    parser.add_argument("--sleep-on-error-s", type=float, default=1.0, help="Sleep after API error/parse failure")

    parser.add_argument(
        "--save-artifacts",
        action="store_true",
        default=True,
        help="Save debug artifacts (code snippet + prompts). Default: True.",
    )
    parser.add_argument(
        "--include-code-in-summary",
        action="store_true",
        default=True,
        help="Include code snippets in vulnerabilities summary. Default: True.",
    )

    args = parser.parse_args()

    def _normalize_lang(v: str) -> str:
        s = (v or "").strip().lower()
        if s in {"java"}:
            return "java"
        if s in {"c", "c++", "cpp", "cxx"}:
            return "c"
        return s

    language = _normalize_lang(args.lang)
    cache_dir = Path(args.cache_dir)
    sensitive_api_map_path = Path(args.sensitive_api_map)
    output_dir = Path(args.output_dir)
    paths = OutputPaths(output_dir=output_dir, run_id=args.run_id, language=language)

    _ensure_dir(output_dir)

    if not cache_dir.exists():
        raise FileNotFoundError(f"cache-dir does not exist: {cache_dir}")

    primevul_path = Path(args.primevul_worklist) if args.primevul_worklist is not None else _PRIMEVUL_TEST_PATH
    use_primevul = primevul_path.exists()
    if use_primevul:
        tasks = list(iter_reasoning_tasks_from_primevul_and_cache(primevul_path, cache_dir))
        legacy_key = True
    else:
        if not sensitive_api_map_path.exists():
            raise FileNotFoundError(f"sensitive-api-map does not exist: {sensitive_api_map_path}")
        sensitive_api_mapping = load_sensitive_api_mapping_for_lang(sensitive_api_map_path, language)
        api_to_cwes = _reverse_cwe_api_map(sensitive_api_mapping)
        tasks = list(iter_reasoning_tasks(cache_dir, api_to_cwes))
        legacy_key = args.legacy_key
    final_results: Dict[str, List[Dict[str, Any]]] = {}
    final_artifacts: Dict[str, Any] = {}
    if args.resume:
        final_results = _load_json(paths.results_path, default={}) or {}
        if args.save_artifacts:
            final_artifacts = _load_json(paths.artifacts_path, default={}) or {}
    runnable: List[Tuple[ReasoningTask, int, int]] = []
    for t in tasks:
        key = t.key(legacy_key=legacy_key)
        existing = final_results.get(key, [])
        if not isinstance(existing, list):
            existing = []
        if len(existing) >= args.rounds:
            continue
        runnable.append((t, args.rounds - len(existing), len(existing)))

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("Missing API key. Set DEEPSEEK_API_KEY.")
    base_url = args.base_url
    try:
        from tqdm import tqdm
    except Exception:
        tqdm = None

    futures = []
    with ThreadPoolExecutor(max_workers=max(1, int(args.workers))) as ex:
        for t, needed_rounds, start_round in runnable:
            futures.append(
                ex.submit(
                    run_reasoning_for_task,
                    task=t,
                    api_key=api_key,
                    base_url=base_url,
                    language=language,
                    model=args.model,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    rounds=needed_rounds,
                    start_round=start_round,
                    timeout_s=args.timeout_s,
                    sleep_on_error_s=args.sleep_on_error_s,
                    legacy_key=legacy_key,
                    save_artifacts=args.save_artifacts,
                )
            )

        iterator = as_completed(futures)
        if tqdm is not None:
            iterator = tqdm(iterator, total=len(futures), desc="reasoning", unit="task")

        for fut in iterator:
            key, rounds, err, artifacts = fut.result()
            if err:
                continue

            if rounds:
                final_results.setdefault(key, [])
                final_results[key].extend(rounds)

            if args.save_artifacts and artifacts is not None:
                final_artifacts[key] = artifacts

    _save_json(paths.results_path, final_results)
    if args.save_artifacts:
        _save_json(paths.artifacts_path, final_artifacts)

    vuln_summary = build_vulnerabilities_summary(
        results=final_results,
        artifacts=final_artifacts,
        include_code=bool(args.include_code_in_summary and args.save_artifacts),
    )
    _save_json(paths.vulnerabilities_path, vuln_summary)

if __name__ == "__main__":
    main()
