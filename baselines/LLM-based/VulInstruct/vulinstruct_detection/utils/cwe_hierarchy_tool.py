
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set
from pathlib import Path
import json

class CWEHierarchyProcessor:
    def __init__(self, cwe_info_file: str):
        self.cwe_info_file = cwe_info_file
        self.cwe_df = None
        self.cwe_dict_tree = {}
        self.cwe_graph = None
        self.top_level_cwes = set()
        
        self._load_and_process_cwe_info()
    
    def _load_and_process_cwe_info(self):
        try:
            self.cwe_df = pd.read_csv(self.cwe_info_file)
            print(f"Loaded CWE info successfully, total {len(self.cwe_df)} records")
            
            self.cwe_df['cwe_unique'] = "CWE-" + self.cwe_df['id'].astype(str)
            self.cwe_df['cwe_str'] = self.cwe_df['cwe_unique']
            
            self._build_hierarchy()
            
        except Exception as e:
            print(f"Failed to load CWE info: {e}")
            raise
    
    def _build_hierarchy(self):
        dummy_df = pd.DataFrame({'cwe_unique': []})
        
        self.cwe_graph = self._generate_graph(dummy_df, self.cwe_df)
        
        for node_obj in self.cwe_graph[0]['children']:
            top_lvl_parent = node_obj['id']
            self.top_level_cwes.add(top_lvl_parent)
            
            self._traverse_tree(node_obj, self.cwe_dict_tree, top_lvl_parent)
            self.cwe_dict_tree[node_obj['id']] = node_obj['id']
        
        print(f"Built CWE hierarchy successfully, top-level CWE nodes: {sorted(self.top_level_cwes)}")
    
    def _generate_graph(self, cve_df_split, cwe_info):
        total = cve_df_split[cve_df_split['cwe_unique'].isin(cwe_info['cwe_str'].unique())].shape[0] if not cve_df_split.empty else 0
        
        data = [
            {
                'id': 'All',
                'datum': total,
                'children': []
            }
        ]

        for row in cwe_info[cwe_info.parent_name.isna()].itertuples():
            pillar_id = row.id
            pillar_cwe_str = row.cwe_str

            children = []
            size = []

            children_rows = cwe_info[cwe_info.parent_id == pillar_id]
            if children_rows.shape[0] > 0:
                for child_row in children_rows.itertuples():
                    child_data = self._generate_graph_helper(child_row, cwe_info, cve_df_split)
                    if child_data["datum"] >= 0:
                        children.append(child_data)
                        size.append(child_data["datum"])

            datum = (cve_df_split[cve_df_split.cwe_unique == pillar_cwe_str].shape[0] if not cve_df_split.empty else 0) + np.sum(size)

            if len(children) > 0:
                instance_data = {
                    "id": pillar_cwe_str,
                    "datum": datum,
                    "children": children,
                    "cwe_str": pillar_cwe_str
                }
            else:
                instance_data = {
                    "id": pillar_cwe_str,
                    "datum": datum,
                    "cwe_str": pillar_cwe_str
                }
            data[0]["children"].append(instance_data)
        
        return data
    
    def _generate_graph_helper(self, row, cwe_info, cve_df_split):
        instance_id = row.id
        instance_cwe_str = row.cwe_str

        children = []
        size = []

        children_rows = cwe_info[cwe_info.parent_id == instance_id]
        if children_rows.shape[0] > 0:
            for child_row in children_rows.itertuples():
                child_data = self._generate_graph_helper(child_row, cwe_info, cve_df_split)
                if child_data["datum"] >= 0:
                    children.append(child_data)
                    size.append(child_data["datum"])

        datum = (cve_df_split[cve_df_split.cwe_unique == instance_cwe_str].shape[0] if not cve_df_split.empty else 0) + np.sum(size)

        if len(children) > 0:
            instance_data = {
                "id": instance_cwe_str,
                "datum": datum,
                "children": children,
                "cwe_str": instance_cwe_str
            }
        else:
            instance_data = {
                "id": instance_cwe_str,
                "datum": datum,
                "cwe_str": instance_cwe_str
            }

        return instance_data
    
    def _traverse_tree(self, node, child_parent, top_lvl_parent):
        if node['id'] not in child_parent:
            child_parent[node['id']] = "<>".join(top_lvl_parent.split("<>")[1:])
        
        if 'children' in node and len(node['children']) > 0:
            for child in node['children']:
                self._traverse_tree(child, child_parent, top_lvl_parent+"<>"+node["id"])
    
    def get_top_cwe_from_exact(self, exact_cwe: str) -> Optional[str]:
        if not exact_cwe or not exact_cwe.strip():
            return None
        
        exact_cwe = exact_cwe.strip()
        
        if exact_cwe in self.top_level_cwes:
            return exact_cwe
        
        if exact_cwe in self.cwe_dict_tree:
            ancestry = self.cwe_dict_tree[exact_cwe]
            
            if exact_cwe not in ancestry:
                ancestry += "<>" + exact_cwe
            
            top_cwe = ancestry.split("<>")[0]
            return top_cwe if top_cwe else exact_cwe
        
        return exact_cwe
    
    def get_top_cwes_from_exact_list(self, exact_cwes: List[str]) -> List[str]:
        top_cwes = []
        seen = set()
        
        for exact_cwe in exact_cwes:
            top_cwe = self.get_top_cwe_from_exact(exact_cwe)
            if top_cwe and top_cwe not in seen:
                top_cwes.append(top_cwe)
                seen.add(top_cwe)
        
        return top_cwes
    
    def get_all_top_level_cwes(self) -> List[str]:
        return sorted(list(self.top_level_cwes))
    
    def validate_cwe_hierarchy(self) -> Dict[str, any]:
        stats = {
            'total_cwes': len(self.cwe_df),
            'top_level_cwes': len(self.top_level_cwes),
            'cwes_in_hierarchy': len(self.cwe_dict_tree),
            'missing_from_hierarchy': []
        }
        
        all_cwes = set(self.cwe_df['cwe_str'].tolist())
        cwes_in_hierarchy = set(self.cwe_dict_tree.keys()) | self.top_level_cwes
        
        missing = all_cwes - cwes_in_hierarchy
        stats['missing_from_hierarchy'] = sorted(list(missing))
        stats['missing_count'] = len(missing)
        
        return stats
    
    def save_hierarchy_info(self, output_file: str):
        hierarchy_info = {
            'top_level_cwes': sorted(list(self.top_level_cwes)),
            'cwe_hierarchy_dict': self.cwe_dict_tree,
            'validation_stats': self.validate_cwe_hierarchy()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(hierarchy_info, f, ensure_ascii=False, indent=2)
        
        print(f"CWE hierarchy info saved to: {output_file}")


def test_cwe_hierarchy():
    cwe_info_file = "/path/to/csv/file"
    
    try:
        processor = CWEHierarchyProcessor(cwe_info_file)
        
        test_cwes = ["CWE-79", "CWE-89", "CWE-120", "CWE-20", "CWE-200"]
        
        print("\nTesting CWE hierarchy derivation:")
        print("-" * 50)
        for cwe in test_cwes:
            top_cwe = processor.get_top_cwe_from_exact(cwe)
            print(f"{cwe} -> {top_cwe}")
        
        print(f"\nTesting batch derivation:")
        print("-" * 50)
        test_list = ["CWE-79", "CWE-89", "CWE-120"]
        top_list = processor.get_top_cwes_from_exact_list(test_list)
        print(f"{test_list} -> {top_list}")
        
        print(f"\nCWE hierarchy validation statistics:")
        print("-" * 50)
        stats = processor.validate_cwe_hierarchy()
        for key, value in stats.items():
            if key != 'missing_from_hierarchy':
                print(f"{key}: {value}")
        
        if stats['missing_from_hierarchy']:
            print(f"Missing CWEs (first 10): {stats['missing_from_hierarchy'][:10]}")
        
        return processor
        
    except Exception as e:
        print(f"Testing failed: {e}")
        return None


if __name__ == "__main__":
    test_cwe_hierarchy()