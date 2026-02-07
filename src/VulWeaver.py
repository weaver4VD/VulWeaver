import json
from operator import contains
import os
import shutil
import subprocess
import sys
import argparse
import Constructing_Enhanced_UDG.joern as joern
from Holistic_Context_Extraction.slice_antman import slicing_multi_method, get_call
from Holistic_Context_Extraction.target import Target
from Constructing_Enhanced_UDG.joern_enhance import get_types, preprocess
from Constructing_Enhanced_UDG.parallel_edges import init_token_stats, get_token_stats, reset_token_stats
from tqdm import tqdm
from Constructing_Enhanced_UDG.common import Language
from Constructing_Enhanced_UDG.codefile import create_code_tree

JOERN_PATH = os.getenv("JOERN_PATH")
current_dir = os.path.dirname(os.path.abspath(__file__))


def get_callgraph(cpg, cpg_dir):
    callgraph = {}
    callgraph['edge'] = {}
    callgraph['node'] = {}
    contains_nodes = {}
    contained_nodes = {}
    from Constructing_Enhanced_UDG.joern import load_cpg_edges, load_cpg_nodes, CPGProxy
    
    if isinstance(cpg, dict):
        print("Loading edge node info from CSV to build Callgraph...")
        edges = load_cpg_edges(cpg_dir)
        nodes = load_cpg_nodes(cpg_dir)
    else:
        edges = cpg.edges(data=True)
        nodes = cpg.nodes
    for edge in edges:
        if len(edge) == 3:
            u, v, d = edge
        else:
            u, v, k, d = edge
            
        if d.get("label") == "CONTAINS":
            if u not in contains_nodes:
                contains_nodes[u] = []
            contains_nodes[u].append(v)
            if v not in contained_nodes:
                contained_nodes[v] = u
    for edge in edges:
        if len(edge) == 3:
            u, v, d = edge
        else:
            u, v, k, d = edge
            
        if d.get("label") == "CALL":
            v_node = nodes.get(v)
            if not v_node or "<operator>" in str(v_node.get('FULL_NAME', '')):
                continue
            
            callee_node = v_node.copy()
            caller_method_id = contained_nodes.get(u)
            
            if caller_method_id is not None:
                if caller_method_id not in callgraph['node']:
                    callgraph['node'][caller_method_id] = nodes[caller_method_id]
                u_node = nodes[u]
                if "callsite" not in callee_node:
                    callee_node["callsite"] = []
                callee_node["callsite"].append(u_node)
                if caller_method_id not in callgraph['edge']:
                    callgraph['edge'][caller_method_id] = []
                callgraph['edge'][caller_method_id].append(callee_node)

    callgraph = refine_callgraph(callgraph)
    with open(f"{cpg_dir}/callgraph_temp.json", "w") as f:
        json.dump(callgraph, f, indent=4)
    return callgraph

def refine_callgraph(callgraph):
    for u in callgraph['edge']:
        for v in callgraph['edge'][u]:
            if "<unresolvedNamespace>" in v.get('FULL_NAME', ''):
                now_v = v
                full_name = v.get('FULL_NAME', '')
                v_name = v.get('NAME', '')
                if not full_name or not v_name:
                    continue
                
                fulltype = full_name.split(".")[0]
                true_fulltype = ""
                
                if not now_v.get('callsite') or 'CODE' not in now_v['callsite'][0]:
                    continue
                
                code_parts = now_v['callsite'][0]['CODE'].split(f".{v_name}")
                if not code_parts:
                    continue
                code = code_parts[0]
                
                for pre_v in callgraph['edge'][u]:
                    if not pre_v.get('callsite') or 'CODE' not in pre_v['callsite'][0]:
                        continue
                    
                    if pre_v['callsite'][0]['CODE'] == code:
                        true_fulltype = pre_v['callsite'][0].get('TYPE_FULL_NAME', '')
                        break
                
                if true_fulltype:
                    v['FULL_NAME'] = f"{true_fulltype}{full_name.replace(fulltype, '')}"
                    for call in v.get('callsite', []):
                        call['METHOD_FULL_NAME'] = v['FULL_NAME']
    
    return callgraph

def get_dangerous_api(callgraph, language):
    """Load sensitive_api from Constructing_Enhanced_UDG/sensitive_api/sensitive_api.json by language."""
    sensitive_api_path = os.path.join(
        current_dir, "Constructing_Enhanced_UDG", "sensitive_api", "sensitive_api.json"
    )
    if not os.path.isfile(sensitive_api_path):
        raise FileNotFoundError(f"sensitive_api file not found: {sensitive_api_path}")
    with open(sensitive_api_path, "r", encoding="utf-8") as fp:
        sensitive_api_all = json.load(fp)
    if language == Language.JAVA:
        lang_key = "java"
    else:
        lang_key = "c"

    sensitive_api = sensitive_api_all.get(lang_key, {})

    api_list = set()
    for cwe in sensitive_api:
        for api in sensitive_api[cwe]:
            api_list.add(api)
    need_judge_api = {}
    for u in callgraph['edge']:
        for v in callgraph['edge'][u]:
            full_name = v.get('FULL_NAME', '')
            if not full_name:
                continue
                
            api_name = full_name.split(":")[0].replace("ANY.", "")
            if api_name in api_list:
                for call in v.get('callsite', []):
                    call_line = call.get('LINE_NUMBER')
                    method_node = callgraph["node"].get(u, {})
                    method_line_start = method_node.get('LINE_NUMBER')
                    method_line_end = method_node.get('LINE_NUMBER_END')
                    if (call_line is not None and 
                        method_line_start is not None and 
                        method_line_end is not None):
                        
                        if int(call_line) >= int(method_line_start) and int(call_line) <= int(method_line_end):
                            filename = method_node.get('FILENAME', 'unknown')
                            method_name = method_node.get('NAME', 'unknown')
                            api_entry = f"{filename}#{method_name}#{call_line}"
                            
                            if api_name not in need_judge_api:
                                need_judge_api[api_name] = []
                            need_judge_api[api_name].append(api_entry)
    return need_judge_api

def pipeline(project_path, cache_path, language, semantic_model_switch=False, format_lambda=False):
    max_workers = 16
    joern.set_joern_env(JOERN_PATH)
    try:
        print(f"🔄 Building target-related directory tree")
        target_repo = Target(
            project_path,
            [],
            language,
            {},
            format_lambda=format_lambda
        )

        analysis_files = target_repo.analysis_files
        create_code_tree(analysis_files, cache_path)
        print(f"✅ Target-related directory tree built successfully")
        target_proj = target_repo.project
    except Exception as e:
        print(f"Error building target-related directory tree: {str(e)}")
        return

    try:
        cpg = joern.export_with_preprocess_and_merge(
            f"{cache_path}/code", cache_path, language, overwrite=False, cdg_need=True, max_workers=max_workers
        )
        assert target_proj is not None
        print(f"🔄 Preprocessing CPG")
        call_node_info = preprocess(cache_path, max_workers=max_workers)
        print(f"✅ CPG preprocessed successfully")
        print(f"🔄 Parsing Project Joern Graph")
        target_proj.load_joern_graph(None, f"{cache_path}/pdg")
        print(f"✅ Project Joern Graph parsed successfully")
    except Exception as e:
        print(f"Error parsing Project Joern Graph: {str(e)}")
        return

    try:
        print(f"🔄 Fetching callgraph")
        callgraph_temp_result = get_callgraph(cpg, f"{cache_path}/cpg")
        print(f"✅ Callgraph fetched successfully")
    except Exception as e:
        print(f"Error fetching callgraph: {str(e)}")
        return

    try:
        print(f"🔄 Fetching semantic model")
        if semantic_model_switch and language == Language.JAVA:
            semantic_model_main_py = os.path.join(os.path.dirname(__file__), "Holistic_Context_Extraction", "semantic_model", "main.py")
            semantic_model_cache_dir = os.path.join(cache_path, "semantic_model")
            subprocess.run(
                [sys.executable, semantic_model_main_py, "--cache_dir", semantic_model_cache_dir, "--code_path", f"{cache_path}/code", "--joern_path", os.environ.get("JOERN_PATH", "")],
                check=True,
                env={**os.environ, "JOERN_PATH": os.environ.get("JOERN_PATH", "")},
            )
            subprocess.run(["mv", f"{semantic_model_cache_dir}/semantic_model.json", f"{cache_path}/cpg/semantic_model.json"], check=True)
            subprocess.run(["mv", f"{semantic_model_cache_dir}/data_depend_dict.json", f"{cache_path}/cpg/data_depend_dict.json"], check=True)
            subprocess.run(["rm", "-rf", semantic_model_cache_dir], check=True)
        print(f"✅ Semantic model fetched successfully")
    except Exception as e:
        semantic_model_switch = False

    try:
        print(f"🔄 Fetching APIs to be judged")
        need_judge_api = get_dangerous_api(callgraph_temp_result, language)
        print(f"✅ APIs to be judged fetched successfully")
    except Exception as e:
        print(f"Error fetching APIs to be judged: {str(e)}")
        return
    
    fp = open(f"{cache_path}/sensitive_api.json", "w")
    json.dump(need_judge_api, fp, indent=4)
    fp.close()

    method_line_mapping = {}
    for sensitive_api in need_judge_api:
        for method in need_judge_api[sensitive_api]:
            line_mapping = int(method.split("#")[-1])
            method_name = method.replace(f"#{line_mapping}", "")
            try:
                method_line_mapping[method_name].append(line_mapping)
            except:
                method_line_mapping[method_name] = [line_mapping]

    cnt = 0
    get_types(f"{cache_path}/cpg")
    for method_name in tqdm(method_line_mapping, total=len(method_line_mapping), desc="Processing methods"):
        target_repo.matching_methods = []
        target_repo.matching_methods.append(f"{method_name}")
        target_repo.line_matching[method_name] = set(method_line_mapping[method_name])
        cache_dir = f"{cache_path}/method/{method_name.replace('/','.')}"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        try:
            print(f"🔄 Fetching targeted callgraph")
            token_stats_file = os.path.join(cache_dir, "token_stats.json")
            init_token_stats(token_stats_file)
            reset_token_stats()
            callgraph = get_call(target_repo, target_proj, cache_dir, max_workers=max_workers, enhanced=True)
            token_stats = get_token_stats()
            print(f"✅ Callgraph fetched successfully")
            print(f"📊 Token usage stats: total calls={token_stats.get('call_count', 0)}, "
                        f"Prompt Tokens={token_stats.get('total_prompt_tokens', 0)}, "
                        f"Completion Tokens={token_stats.get('total_completion_tokens', 0)}, "
                        f"Total Tokens={token_stats.get('total_tokens', 0)}")
            print(f"✅ Targeted callgraph fetched successfully")       
        except Exception as e:
            print(f"Error fetching targeted callgraph: {str(e)}")
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir, ignore_errors=True)
            continue
        try:
            print(f"🔄 Performing targeted slicing")
            if target_repo is not None and target_proj is not None and callgraph is not None:
                callee_name = method_name.split("#")[1]
                slicing_multi_method(target_repo, target_proj, cache_dir, callgraph, language, callee_name, semantic_model_switch)
            print(f"✅ Targeted slicing completed successfully")
        except Exception as e:
            print(f"Error performing targeted slicing for {project_path} {method_name}: {str(e)}")
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir, ignore_errors=True)
            continue

    print("All methods processed")

def main():
    parser = argparse.ArgumentParser(description="VulWeaver: Holistic Context Extraction Pipeline")
    parser.add_argument("--project_path", type=str, required=True, help="Path to the target project directory")
    parser.add_argument("--cache_dir", type=str, required=True, help="Path to the cache directory for storing intermediate results")
    parser.add_argument("--language", type=str, default="java", choices=["java", "c", "cpp"], help="Programming language of the project (default: java)")

    args = parser.parse_args()
    lang_map = {
        "java": Language.JAVA,
        "c": Language.C,
        "cpp": Language.CPP
    }
    language = lang_map[args.language.lower()]

    project_path = os.path.abspath(args.project_path)
    cache_dir = os.path.abspath(args.cache_dir)

    print(f"🚀 Starting pipeline for project: {project_path}")
    print(f"📂 Cache directory: {cache_dir}")
    print(f"🌐 Language: {language.name}")

    pipeline(project_path, cache_dir, language)

if __name__ == "__main__":
    main()
