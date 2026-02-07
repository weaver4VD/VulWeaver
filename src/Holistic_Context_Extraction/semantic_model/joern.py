from __future__ import annotations

import copy
import logging
import os
import subprocess
import sys
import json

import networkx as nx

from common import Language

def set_joern_env(joern_path: str):
    os.environ["PATH"] = joern_path + os.pathsep + os.environ["PATH"]
    assert (
        subprocess.run(["which", "joern"], stdout=subprocess.PIPE)
        .stdout.decode()
        .strip()
        == joern_path + "/joern"
    )
    os.environ["JOERN_HOME"] = joern_path


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
        cpg = nx.nx_agraph.read_dot(os.path.join(cpg_dir, "export.dot"))
        return cpg
    else:
        if os.path.exists(pdg_dir):
            subprocess.run(["rm", "-rf", pdg_dir])
        if os.path.exists(cfg_dir):
            subprocess.run(["rm", "-rf", cfg_dir])
        if os.path.exists(cpg_bin):
            subprocess.run(["rm", "-rf", cpg_bin])
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

    subprocess.run(
        ["joern-export", "--repr", "all", "--out", os.path.abspath(cpg_dir)],
        cwd=output_path,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    cpg = nx.nx_agraph.read_dot(os.path.join(cpg_dir, "export.dot"))
    
    return cpg

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
def preprocess(pdg_dir: str, cfg_dir: str, cpg, need_cdg: bool):
    for pdg_file in os.listdir(pdg_dir):
        file_id = pdg_file.split("-")[0]
        try:
            pdg= nx.nx_agraph.read_dot(
                os.path.join(pdg_dir, pdg_file)
            )
            cfg= nx.nx_agraph.read_dot(
                os.path.join(cfg_dir, f"{file_id}-cfg.dot")
            )
        except Exception as e:
            logging.error(f"Error in reading {pdg_file} or {file_id}-cfg.dot")
            os.remove(os.path.join(pdg_dir, pdg_file))
            os.remove(os.path.join(cfg_dir, f"{file_id}-cfg.dot"))
            continue
        ddg_null_edges = []
        for u, v, k, d in pdg.edges(data=True, keys=True):
            if need_cdg:
                null_edges_label = ["DDG: ", "DDG: this"]
            else:
                null_edges_label = ["DDG: ", "CDG: ", "DDG: this"]
            if d["label"] in null_edges_label:
                ddg_null_edges.append((u, v, k, d))
        pdg.remove_edges_from(ddg_null_edges)

        pdg= nx.compose(pdg, cfg)
        for u, v, k, d in pdg.edges(data=True, keys=True):
            if "label" not in d:
                pdg.edges[u, v, k]["label"] = "CFG"

        method_node = None
        param_nodes = []
        for node in pdg.nodes:
            for key, value in cpg.nodes[node].items():
                pdg.nodes[node][key] = value
            pdg.nodes[node]["NODE_TYPE"] = pdg.nodes[node]["label"]
            node_type = pdg.nodes[node]["NODE_TYPE"]
            if node_type == "METHOD":
                method_node = node
            if node_type == "METHOD_PARAMETER_IN":
                param_nodes.append(node)
            if "CODE" not in pdg.nodes[node]:
                pdg.nodes[node]["CODE"] = ""
            node_code = (
                pdg.nodes[node]["CODE"]
                .replace("\n", "\\n")
                .replace('"', r"__quote__")
                .replace("\\", r"__Backslash__")
            )
            pdg.nodes[node]["CODE"] = (
                pdg.nodes[node]["CODE"]
                .replace("\n", "\\n")
                .replace('"', r"__quote__")
                .replace("\\", r"__Backslash__")
            )
            node_line = (
                pdg.nodes[node]["LINE_NUMBER"]
                if "LINE_NUMBER" in pdg.nodes[node]
                else 0
            )
            node_column = (
                pdg.nodes[node]["COLUMN_NUMBER"]
                if "COLUMN_NUMBER" in pdg.nodes[node]
                else 0
            )
            pdg.nodes[node]["label"] = (
                f"[{node}][{node_line}:{node_column}][{node_type}]: {node_code}"
            )
            if pdg.nodes[node]["NODE_TYPE"] == "METHOD_RETURN":
                pdg.remove_edges_from(list(pdg.in_edges(node)))
        for param_node in param_nodes:
            pdg.add_edge(method_node, param_node, label="DDG")

        nx.nx_agraph.write_dot(pdg, os.path.join(pdg_dir, pdg_file))


def merge(output_path: str, pdg_dir: str, code_dir: str, overwrite: bool = False):
    pdg_old_merge_dir = os.path.join(output_path, "pdg_old_merge")
    if overwrite or not os.path.exists(pdg_old_merge_dir):
        if os.path.exists(pdg_old_merge_dir):
            subprocess.run(["rm", "-rf", pdg_old_merge_dir])
        subprocess.run(["cp", "-r", pdg_dir, pdg_old_merge_dir])
        for pdg_file in os.listdir(pdg_dir):
            try:
                pdg= nx.nx_agraph.read_dot(
                    os.path.join(pdg_dir, pdg_file)
                )
            except Exception as e:
                logging.error(f"Error in reading {pdg_file}")
                os.remove(os.path.join(pdg_dir, pdg_file))
                continue

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
                continue
            if already_merged:
                continue
            if not os.path.exists(os.path.join(code_dir, file_name)):
                continue

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
                    if i == 0:
                        continue
                    in_edges = copy.deepcopy(pdg.in_edges(node, data=True, keys=True))
                    out_edges = copy.deepcopy(pdg.out_edges(node, data=True, keys=True))
                    for u, v, k, d in in_edges:
                        if u == node_line_map[line][0]:
                            continue
                        pdg.add_edge(u, node_line_map[line][0], label=d["label"])
                    for u, v, k, d in out_edges:
                        if v == node_line_map[line][0]:
                            continue
                        pdg.add_edge(node_line_map[line][0], v, label=d["label"])
                    pdg.remove_edges_from(list(in_edges))
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


def export_with_preprocess(
    code_path: str,
    output_path: str,
    language: Language,
    overwrite: bool = False,
    cdg_need: bool = True,
):
    cpg = export(code_path, output_path, language, False)
    pdg_dir = os.path.join(output_path, "pdg")
    cfg_dir = os.path.join(output_path, "cfg")
    cpg_dir = os.path.join(output_path, "cpg")
    pdg_old_dir = os.path.join(output_path, "pdg-old")
    if overwrite or not os.path.exists(pdg_old_dir):
        if os.path.exists(pdg_old_dir):
            subprocess.run(['rm', '-rf', pdg_old_dir])
        subprocess.run(['cp', '-r', pdg_dir, pdg_old_dir])
        preprocess(pdg_dir, cfg_dir, cpg, cdg_need)
    
    return cpg


def export_with_preprocess_and_merge(
    code_path: str,
    output_path: str,
    language: Language,
    overwrite: bool = False,
):
    pdg_dir = os.path.join(output_path, "pdg")
    cpg = export_with_preprocess(code_path, output_path, language, overwrite)
    merge(output_path, pdg_dir, code_path, overwrite)
    return cpg