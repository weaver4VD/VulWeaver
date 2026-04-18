import os
import re
import subprocess
import pandas as pd
import networkx as nx
from networkx.drawing.nx_pydot import write_dot, read_dot
from Constructing_Enhanced_UDG.common import Language

import json
import traceback
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import threading

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

def code_to_neo4jcsv(code_path: str, output_path: str, output_csv_path: str, language: Language):
    os.makedirs(output_path, exist_ok=True)
    if os.path.exists(output_csv_path):
        return
        
    
    cpg_bin = os.path.join(output_path, "cpg.bin")
    if os.path.exists(cpg_bin):
        subprocess.run([
            "joern-export",
            cpg_bin,
            "--repr=all",
            "--format=neo4jcsv",
            f"--out={output_csv_path}"
        ], check=True)
    else:
        subprocess.run(
            ["joern-parse", "--language", language.value, os.path.abspath(code_path)],
            cwd=output_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        subprocess.run([
            "joern-export",
            cpg_bin,
            "--repr=all",
            "--format=neo4jcsv",
            f"--out={output_csv_path}"
        ], check=True)


def process_nodes_file(args):
    csv_path, nodes_file = args
    nodes = pd.read_csv(os.path.join(csv_path, nodes_file), header=None)
    file_label = nodes_file.split('_')[1]
    for i in range(2, len(nodes_file.split('_')) - 1):
        file_label += "_" + nodes_file.split('_')[i]
    header_file = f"nodes_{file_label}_header.csv"
    headers = pd.read_csv(os.path.join(csv_path, header_file), header=None)
    headers_list = headers.iloc[0].tolist()
    headers_list = [str(h).strip().strip(":").split(":")[0] for h in headers_list]
    
    nodes_data = []
    
    for _, row in nodes.iterrows():
        attr = {}
        node_id = None
        node_label = None
        for k, v in zip(headers_list, row):
            if k == "ID":
                node_id = v
                continue
            elif k == "LABEL":
                node_label = str(v)
                continue
            elif k in ["LINE_NUMBER", "LINE_NUMBER_END", "COLUMN_NUMBER", "COLUMN_NUMBER_END"]:
                if pd.notna(v):
                    v = str(int(float(v)))
            if (isinstance(v, str) and (v.startswith("Unnamed") or v == "nan")) or (isinstance(v, float) and pd.isna(v)):
                continue
            attr[k] = v
        nodes_data.append((node_id, node_label, attr))
    
    return nodes_data

def process_edges_file(args):
    csv_path, edges_file = args
    edges = pd.read_csv(os.path.join(csv_path, edges_file), header=None)
    file_label = edges_file.split('_')[1]
    for i in range(2, len(edges_file.split('_')) - 1):
        file_label += "_" + edges_file.split('_')[i]
    header_file = f"edges_{file_label}_header.csv"
    headers = pd.read_csv(os.path.join(csv_path, header_file), header=None)
    headers_list = headers.iloc[0].tolist()
    headers_list = [str(h).strip().strip(":").split(":")[0] for h in headers_list]
    
    edges_data = []
    
    for _, row in edges.iterrows():
        attr = {}
        start_id = None
        end_id = None
        edge_type = None
        for k, v in zip(headers_list, row):
            if k == "START_ID":
                start_id = v
                continue
            elif k == "END_ID":
                end_id = v
                continue
            elif k == "TYPE":
                edge_type = str(v)
                continue
            elif k == "VARIABLE":
                k = "property"
            if (isinstance(v, str) and (v.startswith("Unnamed") or v == "nan")) or (isinstance(v, float) and pd.isna(v)):
                continue
            attr[k] = v
        edges_data.append((start_id, end_id, edge_type, attr))
    
    return edges_data

def neo4jcsv_to_dot(csv_path: str, output_dot_path: str, max_workers: int = 32):
    
    csv_files = os.listdir(csv_path)
    nodes_files = [f for f in csv_files if re.match(r"nodes_.*_data\.csv$", f)]
    edges_files = [f for f in csv_files if re.match(r"edges_.*_data\.csv$", f)]

    G = nx.MultiDiGraph()

    if max_workers is None:
        max_workers = min(len(nodes_files) + len(edges_files), os.cpu_count() * 2)
    
    too_long_ids = set()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        nodes_futures = {executor.submit(process_nodes_file, (csv_path, nodes_file)): nodes_file 
                        for nodes_file in nodes_files}
        
        
        for future in tqdm(as_completed(nodes_futures), total=len(nodes_futures), desc="Process nodes"):
            try:
                nodes_data = future.result()
                for node_id, node_label, attr in nodes_data:
                    if len(attr.get("CODE", "")) >= 16384:
                        too_long_ids.add(node_id)
                        continue
                    G.add_node(node_id, label=node_label, **attr)
            except Exception as e:
                nodes_file = nodes_futures[future]
                
    
    
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        edges_futures = {executor.submit(process_edges_file, (csv_path, edges_file)): edges_file 
                        for edges_file in edges_files}
        
        
        for future in tqdm(as_completed(edges_futures), total=len(edges_futures), desc="Process edges"):
            try:
                edges_data = future.result()
                for start_id, end_id, edge_type, attr in edges_data:
                    if start_id in too_long_ids or end_id in too_long_ids:
                        continue
                    G.add_edge(start_id, end_id, label=edge_type, **attr)
            except Exception as e:
                edges_file = edges_futures[future]
                

    
    
    dot_content = generate_dot_from_graph(G)
    
    
    os.makedirs(os.path.dirname(output_dot_path), exist_ok=True)
    
    
    with open(os.path.join(output_dot_path, "export.dot"), 'w', encoding='utf-8') as f:
        f.write(dot_content)
    
    return G

def generate_dot_from_graph(G: nx.DiGraph) -> str:
    dot_lines = ['digraph {']
    
    
    for node_id, node_attrs in G.nodes(data=True):
        
        label = node_attrs.get('label', '')
        node_str = f'  "{node_id}" [label="{label}"'
        
        
        for attr_name, attr_value in node_attrs.items():
            if attr_name != 'label' and attr_value is not None:
                
                if isinstance(attr_value, str):
                    
                    attr_value = attr_value.replace('"', "'")
                node_str += f' {attr_name}="{attr_value}"'
        
        node_str += '];'
        dot_lines.append(node_str)
    
    
    for source, target, edge_attrs in G.edges(data=True):
        
        label = edge_attrs.get('label', '')
        edge_str = f'  "{source}" -> "{target}"'
        
        if label:
            edge_str += f' [label="{label}"'
            
            
            for attr_name, attr_value in edge_attrs.items():
                if attr_name != 'label' and attr_value is not None:
                    
                    if isinstance(attr_value, str):
                        
                        attr_value = attr_value.replace('"', "'")
                    edge_str += f' {attr_name}="{attr_value}"'
            
            edge_str += ']'
        
        edge_str += ';'
        dot_lines.append(edge_str)
    
    dot_lines.append('}')
    
    return '\n'.join(dot_lines)

def code_to_neo4jcsv_to_dot(code_path: str, output_path: str, csv_path: str, language: Language, max_workers: int = None):
    code_to_neo4jcsv(code_path, output_path, csv_path, Language.JAVA)
    neo4jcsv_to_dot(csv_path, output_path, max_workers)

def process_file(file_name):
    neo4jcache_path = f"neo4jcache/{file_name}Cache"
    os.makedirs(neo4jcache_path, exist_ok=True)

    try:
        code_to_neo4jcsv_to_dot(
            f"test/Gitrepo/{file_name}",
            neo4jcache_path,
            f"neo4jcsv/{file_name}Cache",
            Language.JAVA,
        )
        return None  
    except Exception as e:
        error_info = {
            "file_name": file_name,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        error_log_path = "code2neo4jcsv2dot_error_log.json"

def neo4jcsv_to_dot_multiprocess(csv_path: str, output_dot_path: str, max_workers: int = None):
    
    csv_files = os.listdir(csv_path)
    nodes_files = [f for f in csv_files if re.match(r"nodes_.*_data\.csv$", f)]
    edges_files = [f for f in csv_files if re.match(r"edges_.*_data\.csv$", f)]

    
    if max_workers is None:
        max_workers = min(len(nodes_files) + len(edges_files), os.cpu_count())
    
    nodes_data = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        
        nodes_futures = {executor.submit(process_nodes_file, (csv_path, nodes_file)): nodes_file 
                        for nodes_file in nodes_files}
        
        for future in tqdm(as_completed(nodes_futures), total=len(nodes_futures), desc="Process nodes"):
            try:
                result = future.result()
                nodes_data.extend(result)
            except Exception as e:
                nodes_file = nodes_futures[future]
    
    edges_data = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        
        edges_futures = {executor.submit(process_edges_file, (csv_path, edges_file)): edges_file 
                        for edges_file in edges_files}
        
        for future in tqdm(as_completed(edges_futures), total=len(edges_futures), desc="Process edges"):
            try:
                result = future.result()
                edges_data.extend(result)
            except Exception as e:
                edges_file = edges_futures[future]
    
    G = nx.MultiDiGraph()
    
    
    for node_id, node_label, attr in tqdm(nodes_data, desc="Add nodes to graph"):
        G.add_node(node_id, label=node_label, **attr)
    
    
    for start_id, end_id, edge_type, attr in tqdm(edges_data, desc="Add edges to graph"):
        G.add_edge(start_id, end_id, label=edge_type, **attr)

    
    
    dot_content = generate_dot_from_graph(G)
    
    
    os.makedirs(os.path.dirname(output_dot_path), exist_ok=True)
    
    
    with open(os.path.join(output_dot_path, "export.dot"), 'w', encoding='utf-8') as f:
        f.write(dot_content)      
    
    return G

def code_to_neo4jcsv_to_dot_multiprocess(code_path: str, output_path: str, csv_path: str, language: Language, max_workers: int = None):
    code_to_neo4jcsv(code_path, output_path, csv_path, Language.JAVA)
    neo4jcsv_to_dot_multiprocess(csv_path, output_path, max_workers)