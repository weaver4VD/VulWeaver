from __future__ import annotations

import re
import ast
import copy
import os
import subprocess
import sys
from typing import Any, Optional
from xmlrpc.client import boolean
import cpu_heater
import networkx as nx

from . import joern_node
from .common import Language

import json
import traceback
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from .code2neo4jcsv2dot import neo4jcsv_to_dot

JOERN_PATH = os.getenv("JOERN_PATH")


def set_joern_env(joern_path: str):
    os.environ["PATH"] = joern_path + os.pathsep + os.environ["PATH"]
    assert (
        subprocess.run(["which", "joern"], stdout=subprocess.PIPE)
        .stdout.decode()
        .strip()
        == joern_path + "/joern"
    )
    os.environ["JOERN_HOME"] = joern_path

def load_cpg_nodes(cpg_dir: str) -> dict:
    """Load node attributes from neo4jcsv CPG dir, return dict to save memory"""
    import csv
    node_attr_map = {}
    header_files = [f for f in os.listdir(cpg_dir) if f.startswith("nodes_") and f.endswith("_header.csv")]
    
    for header_file in header_files:
        base_name = header_file.replace("_header.csv", "")
        data_file = base_name + "_data.csv"
        
        header_path = os.path.join(cpg_dir, header_file)
        data_path = os.path.join(cpg_dir, data_file)
        
        if not os.path.exists(data_path):
            continue
        with open(header_path, 'r', encoding='utf-8') as f:
            header_line = f.readline().strip()
            if not header_line:
                continue
            raw_fields = header_line.split(',')
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=raw_fields)
            for row in reader:
                node_id = row.get(':ID') or row.get('id:ID')
                if not node_id: continue
                
                attr = {}
                for k, v in row.items():
                    if not v or v == "<empty>": continue
                    clean_k = k.split(':')[0] if ':' in k and k.split(':')[0] != '' else k
                    if k in [':ID', 'id:ID', ':LABEL', 'label:LABEL']: 
                        continue
                    
                    attr[clean_k] = v
                node_label = row.get(':LABEL') or row.get('label:LABEL')
                if node_label:
                    attr['label'] = node_label
                for int_key in ['LINE_NUMBER', 'LINE_NUMBER_END', 'COLUMN_NUMBER', 'COLUMN_NUMBER_END']:
                    if int_key in attr:
                        try:
                            attr[int_key] = int(attr[int_key])
                        except:
                            pass
                
                node_attr_map[str(node_id)] = attr
                
    return node_attr_map

def load_cpg_method_nodes(cpg_dir: str) -> dict:
    """Load only METHOD node attributes from neo4jcsv CPG dir"""
    import csv
    node_attr_map = {}
    header_path = os.path.join(cpg_dir, "nodes_METHOD_header.csv")
    data_path = os.path.join(cpg_dir, "nodes_METHOD_data.csv")
    
    if not os.path.exists(header_path) or not os.path.exists(data_path):
        return load_cpg_nodes(cpg_dir)
    with open(header_path, 'r', encoding='utf-8') as f:
        header_line = f.readline().strip()
        if not header_line:
            return {}
        raw_fields = header_line.split(',')
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=raw_fields)
        for row in reader:
            node_id = row.get(':ID') or row.get('id:ID')
            if not node_id: continue
            
            attr = {}
            for k, v in row.items():
                if not v or v == "<empty>": continue

                clean_k = k.split(':')[0] if ':' in k and k.split(':')[0] != '' else k

                if k in [':ID', 'id:ID', ':LABEL', 'label:LABEL']: 
                    continue
                
                attr[clean_k] = v

            node_label = row.get(':LABEL') or row.get('label:LABEL')
            attr['label'] = node_label if node_label else "METHOD"

            for int_key in ['LINE_NUMBER', 'LINE_NUMBER_END', 'COLUMN_NUMBER', 'COLUMN_NUMBER_END']:
                if int_key in attr:
                    try:
                        attr[int_key] = int(attr[int_key])
                    except:
                        pass
            
            node_attr_map[str(node_id)] = attr
            
    return node_attr_map

def load_cpg_nodes(cpg_dir: str) -> dict:
    """Load node attributes from neo4jcsv CPG dir, return node_id -> attr dict"""
    import csv
    node_dict = {}
    header_files = [f for f in os.listdir(cpg_dir) if f.startswith("nodes_") and f.endswith("_header.csv")]
    
    for header_file in header_files:
        base_name = header_file.replace("_header.csv", "")
        data_file = base_name + "_data.csv"
        
        header_path = os.path.join(cpg_dir, header_file)
        data_path = os.path.join(cpg_dir, data_file)
        
        if not os.path.exists(data_path):
            continue
        with open(header_path, 'r', encoding='utf-8') as f:
            header_line = f.readline().strip()
            if not header_line:
                continue
            raw_fields = header_line.split(',')
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=raw_fields)
            for row in reader:
                node_id = row.get(':ID') or row.get('id:ID')
                node_label = row.get(':LABEL') or row.get('label:LABEL')
                
                if not node_id: continue
                
                attr = {}
                for k, v in row.items():
                    if not v or v == "<empty>": continue
                    clean_k = k.split(':')[0] if ':' in k and k.split(':')[0] != '' else k
                    if k in [':ID', ':LABEL', 'id:ID', 'label:LABEL']:
                        continue
                    attr[clean_k] = v
                
                attr['label'] = node_label
                node_dict[str(node_id)] = attr
                
    return node_dict

def load_cpg_edges(cpg_dir: str) -> list:
    """Load edge attributes from neo4jcsv CPG dir, return list of tuples to save memory"""
    import csv
    edge_list = []
    header_files = [f for f in os.listdir(cpg_dir) if f.startswith("edges_") and f.endswith("_header.csv")]
    
    for header_file in header_files:
        base_name = header_file.replace("_header.csv", "")
        data_file = base_name + "_data.csv"
        
        header_path = os.path.join(cpg_dir, header_file)
        data_path = os.path.join(cpg_dir, data_file)
        
        if not os.path.exists(data_path):
            continue
        with open(header_path, 'r', encoding='utf-8') as f:
            header_line = f.readline().strip()
            if not header_line:
                continue
            raw_fields = header_line.split(',')
        with open(data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=raw_fields)
            for row in reader:
                start_id = row.get(':START_ID') or row.get('start_id:START_ID')
                end_id = row.get(':END_ID') or row.get('end_id:END_ID')
                edge_type = row.get(':TYPE') or row.get('type:TYPE')
                
                if not start_id or not end_id: continue
                
                attr = {}
                for k, v in row.items():
                    if not v or v == "<empty>": continue
                    clean_k = k.split(':')[0] if ':' in k and k.split(':')[0] != '' else k
                    if k in [':START_ID', ':END_ID', ':TYPE', 'start_id:START_ID', 'end_id:END_ID', 'type:TYPE']:
                        continue
                    attr[clean_k] = v
                    
                attr['label'] = edge_type
                edge_list.append((str(start_id), str(end_id), attr))
                
    return edge_list

class CPGProxy:
    """Lightweight CPG proxy compatible with networkx nodes/edges API"""
    def __init__(self, nodes_dict, edges_list):
        self.nodes_dict = nodes_dict
        self.edges_list = edges_list

    class NodesAccessor:
        def __init__(self, nodes_dict):
            self.nodes_dict = nodes_dict
        def __call__(self, data=False):
            if data: return self.nodes_dict.items()
            return self.nodes_dict.keys()
        def __getitem__(self, key):
            return self.nodes_dict[str(key)]
        def __contains__(self, key):
            return str(key) in self.nodes_dict
        def items(self):
            return self.nodes_dict.items()
        def get(self, key, default=None):
            return self.nodes_dict.get(str(key), default)

    class EdgesAccessor:
        def __init__(self, edges_list):
            self.edges_list = edges_list
        def __call__(self, data=False, keys=False):
            if data and keys:
                return [(u, v, 0, d) for u, v, d in self.edges_list]
            elif data:
                return self.edges_list
            elif keys:
                return [(u, v, 0) for u, v, d in self.edges_list]
            return [(u, v) for u, v, d in self.edges_list]
        def __iter__(self):
            return iter(self.edges_list)

    @property
    def nodes(self):
        return self.NodesAccessor(self.nodes_dict)

    @property
    def edges(self):
        return self.EdgesAccessor(self.edges_list)
    
    def __getitem__(self, node_id):
        return self.nodes_dict[str(node_id)]
    
    def has_node(self, node_id):
        return str(node_id) in self.nodes_dict

def export(
    code_path: str, output_path: str, language: Language, overwrite: bool = False
):
    pdg_dir = os.path.join(output_path, "pdg")
    cfg_dir = os.path.join(output_path, "cfg")
    cpg_dir = os.path.join(output_path, "cpg")
    cpg_bin = os.path.join(output_path, "cpg.bin")
    
    if (
        os.path.exists(pdg_dir)
        and os.path.exists(cfg_dir)
        and os.path.exists(cpg_dir)
        and not overwrite
    ):
        if any(f.startswith("nodes_") for f in os.listdir(cpg_dir)):
            nodes = load_cpg_nodes(cpg_dir)
            edges = load_cpg_edges(cpg_dir)
            return CPGProxy(nodes, edges)
        else:
            return nx.nx_agraph.read_dot(os.path.join(cpg_dir, "export.dot"))
    else:
        if os.path.exists(pdg_dir):
            subprocess.run(["rm", "-rf", pdg_dir])
        if os.path.exists(cfg_dir):
            subprocess.run(["rm", "-rf", cfg_dir])
        if os.path.exists(cpg_dir):
            subprocess.run(["rm", "-rf", cpg_dir])
        if os.path.exists(cpg_bin):
            subprocess.run(["rm", "-rf", cpg_bin])
            
    os.makedirs(output_path, exist_ok=True)
    subprocess.run(
        ["joern-parse", "--language", language.value, os.path.abspath(code_path)],
        cwd=output_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["joern-export", "--repr", "cfg", "--out", os.path.abspath(cfg_dir)],
        cwd=output_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["joern-export", "--repr", "pdg", "--out", os.path.abspath(pdg_dir)],
        cwd=output_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run([
        "joern-export",
        "--repr", "all",
        "--format", "neo4jcsv",
        "--out", os.path.abspath(cpg_dir)
    ], cwd=output_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return load_cpg_nodes(cpg_dir)

def joern_script_run(cpgFile: str, script_path: str, output_path: str):
    subprocess.run(
        [
            "joern",
            "--script",
            script_path,
            "--param",
            f"cpgFile={cpgFile}",
            "--param",
            f"outFile={output_path}",
        ],
        cwd=os.path.dirname(cpgFile),
    )
def _preprocess_single_file(pdg_file: str, pdg_dir: str, cfg_dir: str, cpg, need_cdg: bool):
    """Preprocess a single PDG file (for multi-threading)"""
    file_id = pdg_file.split("-")[0]
    try:
        pdg = nx.nx_agraph.read_dot(
            os.path.join(pdg_dir, pdg_file)
        )
        cfg = nx.nx_agraph.read_dot(
            os.path.join(cfg_dir, f"{file_id}-cfg.dot")
        )
    except Exception as e:
        for d, f in [(pdg_dir, pdg_file), (cfg_dir, f"{file_id}-cfg.dot")]:
            p = os.path.join(d, f)
            if os.path.exists(p): os.remove(p)
        return
    null_labels = {"DDG: ", "DDG: this"}
    if not need_cdg: null_labels.add("CDG: ")
    
    edges_to_remove = [e for e in pdg.edges(data=True, keys=True) if e[3].get("label") in null_labels]
    pdg.remove_edges_from(edges_to_remove)

    pdg = nx.compose(pdg, cfg)
    for u, v, k, d in pdg.edges(data=True, keys=True):
        if "label" not in d: pdg.edges[u, v, k]["label"] = "CFG"
    method_node = None
    param_nodes = []
    def clean_code(c):
        if not c: return ""
        return str(c).replace("\n", "\\n").replace('"', r"__quote__").replace("\\", r"__Backslash__")

    for node in pdg.nodes:
        node_attrs = cpg[node] if isinstance(cpg, dict) else cpg.nodes[node]
        
        for key, value in node_attrs.items():
            pdg.nodes[node][key] = value
            
        node_type = pdg.nodes[node].get("label", "")
        pdg.nodes[node]["NODE_TYPE"] = node_type
        
        if node_type == "METHOD":
            method_node = node
        elif node_type == "METHOD_PARAMETER_IN":
            param_nodes.append(node)
            
        raw_code = pdg.nodes[node].get("CODE", "")
        node_code = clean_code(raw_code)
        pdg.nodes[node]["CODE"] = node_code
        
        line = pdg.nodes[node].get("LINE_NUMBER", 0)
        col = pdg.nodes[node].get("COLUMN_NUMBER", 0)
        pdg.nodes[node]["label"] = f"[{node}][{line}:{col}][{node_type}]: {node_code}"
        
        if node_type == "METHOD_RETURN":
            pdg.remove_edges_from(list(pdg.in_edges(node)))

    if method_node:
        for param_node in param_nodes:
            pdg.add_edge(method_node, param_node, label="DDG")

    nx.nx_agraph.write_dot(pdg, os.path.join(pdg_dir, pdg_file))


def preprocess(pdg_dir: str, cfg_dir: str, cpg, need_cdg: bool, max_workers: int = None):
    """Preprocess PDG files in parallel"""
    pdg_files = [f for f in os.listdir(pdg_dir) if f.endswith(".dot")]
    if not pdg_files: return
    
    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) + 4)
    max_workers = min(max_workers, 16)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_preprocess_single_file, pdg_file, pdg_dir, cfg_dir, cpg, need_cdg): pdg_file 
                  for pdg_file in pdg_files}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Preprocessing PDG files"):
            try:
                future.result()
            except Exception:
                pass


def _merge_single_pdg_file(pdg_file: str, pdg_dir: str, code_dir: str):
    """Merge a single PDG file (for multi-threading)"""
    try:
        pdg = nx.nx_agraph.read_dot(
            os.path.join(pdg_dir, pdg_file)
        )
    except Exception as e:
        os.remove(os.path.join(pdg_dir, pdg_file))
        return

    node_line_map = {}
    file_name = ""
    already_merged = False
    for node in pdg.nodes:
        if "INCLUDE_ID" in pdg.nodes[node].keys():
            already_merged = True
        if "CODE" not in pdg.nodes[node]:
            pdg.nodes[node]["CODE"] = ""
        node_line = (
            pdg.nodes[node]["LINE_NUMBER"]
            if "LINE_NUMBER" in pdg.nodes[node]
            else 0
        )
        if "FILENAME" in pdg.nodes[node].keys():
            file_name = pdg.nodes[node]["FILENAME"]
        node_type = pdg.nodes[node]["NODE_TYPE"]
        if node_type == "METHOD":
            continue
        try:
            node_line_map[node_line].append(node)
        except:
            node_line_map[node_line] = [node]
    if file_name == "":
        return
    if already_merged:
        return
    if not os.path.exists(os.path.join(code_dir, file_name)):
        return

    fp = open(os.path.join(code_dir, file_name))
    full_code = fp.readlines()
    fp.close()
    for line in node_line_map:
        max_col = 0
        min_col = sys.maxsize
        if int(line) - 1 >= len(full_code):
            continue
        new_node = pdg.nodes[node_line_map[line][0]].copy()
        new_node["label"] = (
            full_code[int(line) - 1]
            .strip()
            .replace(r'"', r"__quote__")
            .replace("\\", r"__Backslash__")
        )
        raw_code = pdg.nodes[node_line_map[line][0]]["CODE"]
        new_node["CODE"] = (
            full_code[int(line) - 1]
            .strip()
            .replace(r'"', r"__quote__")
            .replace("\\", r"__Backslash__")
        )
        new_node["INCLUDE_ID"] = {line: node_line_map[line]}
        for node in node_line_map[line]:
            if node == node_line_map[line][0]:
                code = raw_code
            else:
                code = pdg.nodes[node]["CODE"]
            for key, value in pdg.nodes[node].items():
                if key in [
                    "label",
                    "LINE_NUMBER",
                    "CODE",
                    "FILENAME",
                    "FULL_NAME",
                    "LINE_NUMBER_END",
                ]:
                    continue
                if key == "COLUMN_NUMBER":
                    min_col = min(min_col, int(value))
                    continue
                if key == "COLUMN_NUMBER_END":
                    max_col = max(max_col, int(value))
                    continue
                try:
                    new_node[key].append(value)
                except:
                    new_node[key] = [value]
        new_node["COLUMN_NUMBER"] = min_col
        new_node["COLUMN_NUMBER_END"] = max_col
        for key, value in new_node.items():
            pdg.nodes[node_line_map[line][0]][key] = value
        for i, node in enumerate(node_line_map[line]):
            in_edges = copy.deepcopy(pdg.in_edges(node, data=True, keys=True))
            out_edges = copy.deepcopy(pdg.out_edges(node, data=True, keys=True))
            for u, v, k, d in in_edges:
                if u in node_line_map[line]:
                    continue
                pdg.add_edge(u, node_line_map[line][0], label=d["label"])
            for u, v, k, d in out_edges:
                if v in node_line_map[line]:
                    continue
                pdg.add_edge(node_line_map[line][0], v, label=d["label"])
            pdg.remove_edges_from(list(in_edges))
            if i != 0:
                pdg.remove_node(node)

    edges = set()
    edge_key_map = {}
    raw_edges = copy.deepcopy(pdg.edges(data=True, keys=True))
    for u, v, k, d in raw_edges:
        if f"{u}__split__{v}__split__{d['label']}" in edges:
            edge_key = edge_key_map[f"{u}__split__{v}__split__{d['label']}"]
            pdg.remove_edge(u, v, key = edge_key)
            edge_key_map[f"{u}__split__{v}__split__{d['label']}"] = k
        else:
            edges.add(f"{u}__split__{v}__split__{d['label']}")
            edge_key_map[f"{u}__split__{v}__split__{d['label']}"] = k
    nx.nx_agraph.write_dot(pdg, os.path.join(pdg_dir, pdg_file))


def merge(output_path: str, pdg_dir: str, code_dir: str, overwrite: bool = False, max_workers: int = None):
    """Merge PDG files in parallel"""
    pdg_old_merge_dir = os.path.join(output_path, "pdg_old_merge")
    if overwrite or not os.path.exists(pdg_old_merge_dir):
        if os.path.exists(pdg_old_merge_dir):
            subprocess.run(["rm", "-rf", pdg_old_merge_dir])
        subprocess.run(["cp", "-r", pdg_dir, pdg_old_merge_dir])
        
        pdg_files = [f for f in os.listdir(pdg_dir) if f.endswith(".dot")]
        if not pdg_files: return
        
        if max_workers is None:
            max_workers = min(32, (os.cpu_count() or 1) + 4)
        max_workers = min(max_workers, 16)
        work_list = [(pdg_file, pdg_dir, code_dir) for pdg_file in pdg_files]
        cpu_heater.multiprocess(_merge_single_pdg_file, work_list, max_workers=max_workers, show_progress=True)


def add_cfg_lines(
    output_path: str, pdg_dir: str, code_dir: str, cpg_dir: str, overwrite: bool = False
):
    pdg_old_add_var_def_dir = os.path.join(output_path, "pdg_old_def")
    if overwrite or not os.path.exists(pdg_old_add_var_def_dir):
        if os.path.exists(pdg_old_add_var_def_dir):
            subprocess.run(["rm", "-rf", pdg_old_add_var_def_dir])
        subprocess.run(["cp", "-r", pdg_dir, pdg_old_add_var_def_dir])


        cpg = neo4jcsv_to_dot(cpg_dir, cpg_dir)
        ids = set()
        for node in cpg.nodes:
            ids.add(node)
        max_id = max(ids) + 1
        for pdg_file in os.listdir(pdg_dir):
            try:
                pdg= nx.nx_agraph.read_dot(
                    os.path.join(pdg_dir, pdg_file)
                )
            except Exception as e:
                print(f"Error in reading {pdg_file}")
                os.remove(os.path.join(pdg_dir, pdg_file))
                continue
            file_name = ""
            method_node = None
            lines = set()
            line_node_map = {}
            for node in pdg.nodes:
                node_line = (
                    pdg.nodes[node]["LINE_NUMBER"]
                    if "LINE_NUMBER" in pdg.nodes[node]
                    else 0
                )
                line_node_map[int(node_line)] = node
                lines.add(int(node_line))
                if "FILENAME" in pdg.nodes[node].keys():
                    file_name = pdg.nodes[node]["FILENAME"]
                if pdg.nodes[node]["NODE_TYPE"] == "METHOD":
                    method_node = node
                elif "LINE_NUMBER_END" in pdg.nodes[node].keys():
                    lines.add(
                        i
                        for i in range(
                            int(pdg.nodes[node]["LINE_NUMBER"]),
                            int(pdg.nodes[node]["LINE_NUMBER_END"] + 1),
                        )
                    )
            if method_node is None:
                continue
            if not os.path.exists(os.path.join(code_dir, file_name)):
                continue
            fp = open(os.path.join(code_dir, file_name))
            full_code = fp.readlines()
            fp.close()
            line = int(pdg.nodes[method_node]["LINE_NUMBER"])
            if "LINE_NUMBER_END" not in pdg.nodes[method_node].keys():
                continue
            while line < int(pdg.nodes[method_node]["LINE_NUMBER_END"]):
                if line in lines:
                    line += 1
                    continue
                if (line-1<len(full_code)):
                    break
                if (
                    full_code[line - 1]
                    .replace(" ", "")
                    .replace("{", "")
                    .replace("}", "")
                    .replace("\t", "")
                    .replace("\n", "")
                    .replace("(", "")
                    .replace(")", "")
                    == ""
                ):
                    line += 1
                    continue

                new_node_attr = {
                    "CODE": full_code[int(line) - 1]
                    .strip()
                    .replace(r'"', r"__quote__")
                    .replace("\\", r"__Backslash__"),
                    "label": full_code[int(line) - 1]
                    .strip()
                    .replace(r'"', r"__quote__")
                    .replace("\\", r"__Backslash__"),
                    "INCLUDE_ID": {line: max_id},
                    "LINE_NUMBER": line,
                    "NODE_TYPE": ["variable_declaration"],
                }

                pdg.add_node(max_id, **new_node_attr)
                if line - 1 in line_node_map.keys():
                    pdg.add_edge(line_node_map[line - 1], max_id, label="CFG")
                if line + 1 in lines and line + 1 in line_node_map.keys():
                    pdg.add_edge(max_id, line_node_map[line + 1], label="CFG")
                line_node_map[line] = max_id
                max_id += 1
                line += 1
            nx.nx_agraph.write_dot(pdg, os.path.join(pdg_dir, pdg_file))


def export_with_preprocess(
    code_path: str,
    output_path: str,
    language: Language,
    overwrite: bool = False,
    cdg_need: bool = True,
    max_workers: int = None,
    need_full_graph: bool = False
):
    """Export and preprocess; support loading full graph or node attributes only"""
    cpg_data = export(code_path, output_path, language, overwrite)
    pdg_dir = os.path.join(output_path, "pdg")
    cfg_dir = os.path.join(output_path, "cfg")
    pdg_old_dir = os.path.join(output_path, "pdg-old")
    
    if overwrite or not os.path.exists(pdg_old_dir):
        if os.path.exists(pdg_old_dir):
            subprocess.run(['rm', '-rf', pdg_old_dir])
        subprocess.run(['cp', '-r', pdg_dir, pdg_old_dir])
        preprocess(pdg_dir, cfg_dir, cpg_data, cdg_need, max_workers)
    if need_full_graph and isinstance(cpg_data, dict):
        cpg_dir = os.path.join(output_path, "cpg")
        return neo4jcsv_to_dot(cpg_dir, cpg_dir)
        
    return cpg_data


def export_with_preprocess_and_merge(
    code_path: str,
    output_path: str,
    language: Language,
    overwrite: bool = False,
    cdg_need: bool = True,
    max_workers: int = None,
    need_full_graph: bool = False
):
    pdg_dir = os.path.join(output_path, "pdg")
    cpg = export_with_preprocess(code_path, output_path, language, overwrite, cdg_need, max_workers, need_full_graph)
    merge(output_path, pdg_dir, code_path, overwrite, max_workers)
    return cpg


class CPGNode:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.attr = {}

    def get_value(self, key: str) -> Optional[str]:
        if key in self.attr:
            return self.attr[key]
        else:
            return None

    def set_attr(self, key: str, value: str):
        self.attr[key] = value


class Edge:
    def __init__(self, edge_id: tuple[int, int]):
        self.edge_id = edge_id
        self.attr: list[tuple[int, int]] = []

    def set_attr(self, key, value):
        self.attr.append((key, value))


class CPG:
    def __init__(self, cpg_dir: str):

        self.g = neo4jcsv_to_dot(cpg_dir, cpg_dir)

    def get_node(self, node_id: int) -> dict[str, str]:
        return self.g.nodes[node_id]

    def _init__(self, cpg_dir: str):
        self.cpg_dir = cpg_dir
        cpg_path = os.path.join(cpg_dir, "export.dot")
        if not os.path.exists(cpg_path):
            raise FileNotFoundError(f"export.dot is not found in {cpg_path}")
        cpg_nx = nx.nx_agraph.read_dot(cpg_path)
        self.g = nx.MultiDiGraph()
        for nx_node in cpg_nx.nodes():
            node_type = cpg_nx.nodes[nx_node]["label"]
            node = self._parser_node(node_type, int(nx_node), cpg_nx.nodes[nx_node])
            self.g.add_node(int(nx_node), **node.to_dict())
        for u, v, data in cpg_nx.edges(data=True):
            src = int(u)
            dst = int(v)
            self.g.add_edge(src, dst, **data)

    def _parser_node(self, node_type: str, node_id: int, node_attr: dict[str, str]):
        Node = getattr(joern_node, node_type)
        attr: dict[str, Any] = {}
        for key in Node.__dataclass_fields__.keys():
            if key.upper() in node_attr:
                if key in [
                    "line_number",
                    "column_number",
                    "line_number_end",
                    "column_number_end",
                    "order",
                    "argument_index",
                    "index",
                ]:
                    attr[key] = int(node_attr[key.upper()])
                elif key in ["is_external", "is_variadic"]:
                    attr[key] = bool(node_attr[key.upper()])
                else:
                    attr[key] = node_attr[key.upper()]
        node: joern_node.NODE = Node(id=node_id, **attr)
        return node


class PDGNode:
    def __init__(self, node_id: int, attr: dict[str, str], pdg: PDG):
        self.node_id: int = node_id
        self.attr: dict[str, str] = attr
        self.pdg: PDG = pdg
        self.is_patch_node = False

    def __hash__(self):
        return hash(self.node_id)

    def __eq__(self, node: object):
        if not isinstance(node, PDGNode):
            return False
        if self.node_id == node.node_id:
            return True
        else:
            return False

    @property
    def line_number(self) -> Optional[int]:
        if "LINE_NUMBER" not in self.attr:
            return None
        return int(self.attr["LINE_NUMBER"])

    @property
    def line_number_end(self) -> Optional[int]:
        if "LINE_NUMBER_END" not in self.attr:
            return None
        return int(self.attr["LINE_NUMBER_END"])

    @property
    def type(self) -> str:
        return self.attr["NODE_TYPE"]

    @property
    def code(self) -> str:
        if "CODE" not in self.attr:
            return ""
        return (
            self.attr["CODE"]
            .replace(r"__quote__", r'"')
            .replace("__Backslash__", r"\\")
        )

    @property
    def get_successors(self) -> list[PDGNode]:
        nodes = []
        for node in self.pdg.g.successors(self.node_id):
            nodes.append(PDGNode(node, self.pdg.g.nodes[node], self.pdg))
        return nodes

    @property
    def get_predecessors(self) -> list[PDGNode]:
        nodes = []
        for node in self.pdg.g.predecessors(self.node_id):
            nodes.append(PDGNode(node, self.pdg.g.nodes[node], self.pdg))
        return nodes

    def get_predecessors_by_label(self, label: str) -> list[tuple[PDGNode, str]]:
        nodes = []
        for node in self.pdg.g.predecessors(self.node_id):
            for _, edge in self.pdg.g[node][self.node_id].items():
                if edge["label"].startswith(label):
                    nodes.append(
                        (PDGNode(node, self.pdg.g.nodes[node], self.pdg), edge["label"])
                    )
        return nodes

    def get_successors_by_label(self, label: str) -> list[tuple[PDGNode, str]]:
        nodes = []
        for node in self.pdg.g.successors(self.node_id):
            for _, edge in self.pdg.g[self.node_id][node].items():
                if edge["label"].startswith(label):
                    nodes.append(
                        (PDGNode(node, self.pdg.g.nodes[node], self.pdg), edge["label"])
                    )
        return nodes

    @property
    def pred_cfg_nodes(self) -> list[PDGNode]:
        pred = self.get_predecessors_by_label("CFG")
        return [node for node, _ in pred]

    @property
    def succ_cfg_nodes(self) -> list[PDGNode]:
        succ = self.get_successors_by_label("CFG")
        return [node for node, _ in succ]

    @property
    def pred_ddg_nodes(self) -> list[PDGNode]:
        pred = self.get_predecessors_by_label("DDG")
        return [node for node, _ in pred]

    @property
    def pred_cdg(self) -> list[PDGNode]:
        pred = self.get_predecessors_by_label("CDG")
        return [node for node, _ in pred]

    @property
    def succ_cdg(self) -> list[PDGNode]:
        succ = self.get_successors_by_label("CDG")
        return [node for node, _ in succ]

    @property
    def pred_ddg(self) -> list[tuple[PDGNode, str]]:
        pred_ddg = self.get_predecessors_by_label("DDG")
        pred_ddg = [(node, e.replace("DDG: ", "")) for node, e in pred_ddg]
        return pred_ddg

    @property
    def succ_ddg(self) -> list[tuple[PDGNode, str]]:
        succ_ddg = self.get_successors_by_label("DDG")
        succ_ddg = [(node, e.replace("DDG: ", "")) for node, e in succ_ddg]
        return succ_ddg

    @property
    def succ_ddg_nodes(self) -> list[PDGNode]:
        succ = self.get_successors_by_label("DDG")
        return [node for node, _ in succ]

    def add_attr(self, key: str, value: str):
        self.attr[key] = value


class PDG:
    def __init__(self, pdg_path: str) -> None:
        self.pdg_path = pdg_path
        if not os.path.exists(self.pdg_path):
            raise FileNotFoundError(f"dot file is not found in {self.pdg_path}")

        self.g= nx.nx_agraph.read_dot(pdg_path)
        self.method_node = None
        for node in self.g.nodes():
            if self.g.nodes[node]["NODE_TYPE"] == "METHOD":
                self.method_node = node
                break

        self.line_map_method_nodes = {int(self.g.nodes[self.method_node]["LINE_NUMBER"]): [self.method_node]}
        for node in self.g.nodes():
            if "INCLUDE_ID" not in self.g.nodes[node].keys():
                continue
            else:
                self.line_map_method_nodes.update(
                    ast.literal_eval(self.g.nodes[node]["INCLUDE_ID"])
                )

    @property
    def method_node_id(self):
        return self.method_node

    @property
    def line_map_method_nodes_id(self):
        return self.line_map_method_nodes

    @property
    def filename(self) -> Optional[str]:
        if self.method_node == None or "FILENAME" not in self.g.nodes[self.method_node]:
            return None
        return self.g.nodes[self.method_node]["FILENAME"]

    @property
    def line_number(self) -> Optional[int]:
        if (
            self.method_node is None
            or "LINE_NUMBER" not in self.g.nodes[self.method_node]
        ):
            return None
        return int(self.g.nodes[self.method_node]["LINE_NUMBER"])

    @property
    def name(self) -> Optional[str]:
        if self.method_node == None:
            return None
        if "NAME" not in self.g.nodes[self.method_node].keys():
            return None
        if self.g.nodes[self.method_node]["NAME"] == "<init>":
            match = re.search(r'(?:^|[$.])([A-Za-z_]\w*)(?=\.<init>)', self.g.nodes[self.method_node]["FULL_NAME"])
            if match:
                return match.group(1)
            else:
                return self.g.nodes[self.method_node]["FILENAME"].split(".java")[0].split("/")[-1]
        return self.g.nodes[self.method_node]["NAME"]

    def get_node(self, node_id) -> PDGNode:
        return PDGNode(node_id, self.g.nodes[node_id], self)

    def get_nodes_by_line_number(self, line_number: int) -> list[PDGNode]:
        nodes: list[PDGNode] = []
        for node, attr in self.g.nodes.items():
            if "LINE_NUMBER" not in attr:
                continue
            if attr["LINE_NUMBER"] == str(line_number):
                pdg_node = PDGNode(node, attr, self)
                nodes.append(pdg_node)
        return nodes

def get_callgraph_from_joern(cpg_dir: str):
    if os.path.exists(os.path.join(cpg_dir, "callgraph.json")):
        with open(os.path.join(cpg_dir, "callgraph.json"), "r") as f:
            callgraph = json.load(f)
    else:
        subprocess.run(
            ["joern", "--script", "scripts/get_callgraph.sc", "--param", f"cpgFile={cpg_dir}/../cpg.bin", "--param", f"output={cpg_dir}/callgraph.json"]
        )
        with open(os.path.join(cpg_dir, "callgraph.json"), "r") as f:
            callgraph = json.load(f)
    return callgraph