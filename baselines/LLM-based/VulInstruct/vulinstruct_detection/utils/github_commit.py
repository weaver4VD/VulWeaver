
import requests
import re
from typing import List, Dict, Tuple

class SimpleDiffExtractor:
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (diff extractor)'
        })
    
    def get_diff(self, commit_url: str) -> str:
        if not commit_url.endswith('.diff'):
            diff_url = commit_url + '.diff'
        else:
            diff_url = commit_url
            
        response = self.session.get(diff_url)
        response.raise_for_status()
        return response.text
    
    def extract_function_context(self, diff_lines: List[str], change_line_idx: int) -> str:
        for i in range(change_line_idx, -1, -1):
            line = diff_lines[i]
            
            if line.startswith('@@') or line.startswith('+++') or line.startswith('---'):
                continue
                
            clean_line = line[1:] if line.startswith(('+', '-', ' ')) else line
            clean_line = clean_line.strip()
            
            function_patterns = [
                r'^\w+.*\s+(\w+)\s*\([^)]*\)\s*\{?$',
                r'^\s*(?:public|private|protected)?\s*function\s+(\w+)\s*\(',
                r'^\s*(?:function\s+(\w+)|(\w+)\s*:\s*function|\s*(\w+)\s*\([^)]*\)\s*\{)',
                r'^\s*def\s+(\w+)\s*\(',
                r'^\s*(?:public|private|protected)?\s*(?:static\s+)?[^=]*\s+(\w+)\s*\([^)]*\)\s*\{?'
            ]
            
            for pattern in function_patterns:
                match = re.search(pattern, clean_line)
                if match:
                    for group in match.groups():
                        if group:
                            return group
        
        return "unknown_function"
    
    def parse_diff_changes(self, diff_text: str) -> List[Dict]:
        lines = diff_text.split('\n')
        changes = []
        current_file = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if line.startswith('diff --git'):
                file_match = re.search(r'a/(.+?)\s+b/(.+)', line)
                if file_match:
                    current_file = file_match.group(1)
            
            elif line.startswith('@@'):
                hunk_match = re.search(r'@@\s*-\d+,?\d*\s*\+\d+,?\d*\s*@@(.*)$', line)
                hunk_context = hunk_match.group(1).strip() if hunk_match else ""
                
                i += 1
                while i < len(lines) and not lines[i].startswith(('diff', '@@')):
                    change_line = lines[i]
                    
                    if change_line.startswith(('+', '-')) and not change_line.startswith(('+++', '---')):
                        function_name = self.extract_function_context(lines, i)
                        
                        if hunk_context and '(' in hunk_context:
                            func_match = re.search(r'(\w+)\s*\(', hunk_context)
                            if func_match:
                                function_name = func_match.group(1)
                        
                        changes.append({
                            'file': current_file or 'unknown_file',
                            'function': function_name,
                            'change_type': 'addition' if change_line.startswith('+') else 'deletion',
                            'line_content': change_line[1:].strip(),
                            'raw_line': change_line
                        })
                    
                    i += 1
                continue
            
            i += 1
        
        return changes
    
    def group_changes_by_function(self, changes: List[Dict]) -> Dict[str, Dict]:
        grouped = {}
        
        for change in changes:
            key = f"{change['file']}::{change['function']}"
            
            if key not in grouped:
                grouped[key] = {
                    'file': change['file'],
                    'function': change['function'],
                    'additions': [],
                    'deletions': []
                }
            
            if change['change_type'] == 'addition':
                grouped[key]['additions'].append(change['line_content'])
            else:
                grouped[key]['deletions'].append(change['line_content'])
        
        return grouped
    
    def extract_from_commit_url(self, commit_url: str) -> Dict:
        try:
            diff_text = self.get_diff(commit_url)
            
            changes = self.parse_diff_changes(diff_text)
            
            grouped_changes = self.group_changes_by_function(changes)
            
            return {
                'commit_url': commit_url,
                'status': 'success',
                'total_changes': len(changes),
                'functions_modified': len(grouped_changes),
                'changes_by_function': grouped_changes,
                'raw_changes': changes
            }
            
        except Exception as e:
            return {
                'commit_url': commit_url,
                'status': 'error',
                'error': str(e)
            }

def demo_extraction():
    extractor = SimpleDiffExtractor()
    
    test_url = "https://github.com/octobercms/library/commit/5bd1a28140b825baebe6becd4f7562299d3de3b9"
    
    print(f"Extracting commit: {test_url}")
    result = extractor.extract_from_commit_url(test_url)
    
    if result['status'] == 'success':
        print(f"\n=== Extraction Results ===")
        print(f"Total changes: {result['total_changes']}")
        print(f"Functions modified: {result['functions_modified']}")
        
        print(f"\n=== Changes Grouped by Function ===")
        for func_key, func_data in result['changes_by_function'].items():
            print(f"\n📁 {func_data['file']}")
            print(f"🔧 Function: {func_data['function']}")
            
            if func_data['deletions']:
                print("  ❌ Deleted code:")
                for deletion in func_data['deletions']:
                    print(f"    - {deletion}")
            
            if func_data['additions']:
                print("  ✅ Added code:")
                for addition in func_data['additions']:
                    print(f"    + {addition}")
        
        print(f"\n=== Core Data Structure ===")
        simple_output = {}
        for func_key, func_data in result['changes_by_function'].items():
            simple_output[func_key] = {
                'before': func_data['deletions'],
                'after': func_data['additions']
            }
        
        import json
        print(json.dumps(simple_output, indent=2, ensure_ascii=False))
        
    else:
        print(f"❌ Extraction failed: {result['error']}")

if __name__ == "__main__":
    demo_extraction()