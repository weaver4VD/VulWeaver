
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from cwe_hierarchy_tool import CWEHierarchyProcessor

class SimpleCWERelationChecker:
    def __init__(self, cwe_info_file: str):
        self.processor = CWEHierarchyProcessor(cwe_info_file)
        
    def check_relationship(self, cwe1: str, cwe2: str) -> tuple:
        if not cwe1.startswith("CWE-"):
            cwe1 = f"CWE-{cwe1}"
        if not cwe2.startswith("CWE-"):
            cwe2 = f"CWE-{cwe2}"
            
        if cwe1 == cwe2:
            return "same", f"Both are {cwe1}"
        
        top_cwe1 = self.processor.get_top_cwe_from_exact(cwe1)
        top_cwe2 = self.processor.get_top_cwe_from_exact(cwe2)
        
        in_hierarchy1 = cwe1 in self.processor.cwe_dict_tree
        in_hierarchy2 = cwe2 in self.processor.cwe_dict_tree
        
        if not in_hierarchy1 and not in_hierarchy2:
            return "unknown", f"Both CWEs not found in hierarchy"
        elif not in_hierarchy1:
            return "unknown", f"{cwe1} not found in hierarchy"
        elif not in_hierarchy2:
            return "unknown", f"{cwe2} not found in hierarchy"
        
        path1 = self.processor.cwe_dict_tree.get(cwe1, "")
        path2 = self.processor.cwe_dict_tree.get(cwe2, "")
        
        ancestors1 = path1.split("<>") if path1 else []
        ancestors2 = path2.split("<>") if path2 else []
        
        if cwe2 in ancestors1:
            return "ancestor-descendant", f"{cwe2} is ancestor of {cwe1}"
        if cwe1 in ancestors2:
            return "ancestor-descendant", f"{cwe1} is ancestor of {cwe2}"
        
        if top_cwe1 == top_cwe2:
            return "same-branch", f"Both under {top_cwe1} branch"
        
        return "different-branches", f"{cwe1} under {top_cwe1}, {cwe2} under {top_cwe2}"

def main():
    cwe_info_file = "/path/to/csv/file"
    
    checker = SimpleCWERelationChecker(cwe_info_file)
    
    test_pairs = [
        ("CWE-787", "CWE-119"),
        ("CWE-416", "CWE-825"),
        ("CWE-89", "CWE-943"),
        ("CWE-787", "CWE-787"),
        ("CWE-200", "CWE-522"),
        ("CWE-119", "CWE-787"),
        ("CWE-20", "CWE-79"),
    ]
    
    print("CWE Relationship Analysis")
    print("=" * 60)
    
    for cwe1, cwe2 in test_pairs:
        rel_type, description = checker.check_relationship(cwe1, cwe2)
        print(f"\n{cwe1} <-> {cwe2}")
        print(f"  Relationship type: {rel_type}")
        print(f"  Description: {description}")
        
        top1 = checker.processor.get_top_cwe_from_exact(cwe1)
        top2 = checker.processor.get_top_cwe_from_exact(cwe2)
        if top1 != cwe1 or top2 != cwe2:
            print(f"  Top-level CWE: {cwe1}->{top1}, {cwe2}->{top2}")

if __name__ == "__main__":
    main()