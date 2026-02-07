"""
Batch clone repositories required for PrimeVul dataset
Supports resumable downloads, progress display, and status recording
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Set
import argparse
from tqdm import tqdm
import hashlib

from url_parser import CommitURLParser


class BatchRepositoryCloner:
    """Batch Repository Cloner"""
    
    def __init__(self, projects_dir: str = "../projects", status_file: str = "./clone_status.json"):
        self.projects_dir = os.path.abspath(projects_dir)
        self.status_file = os.path.abspath(status_file)
        self.parser = CommitURLParser()
        os.makedirs(self.projects_dir, exist_ok=True)
        self.status = self.load_status()
        self.stats = {
            'total_repos': 0,
            'already_cloned': 0,
            'newly_cloned': 0,
            'failed': 0,
            'skipped': 0
        }

    def load_status(self) -> Dict:
        """Load clone status"""
        if os.path.exists(self.status_file):
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Unable to load status file {self.status_file}: {e}")
                return {}
        return {}

    def save_status(self):
        """Save clone status"""
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(self.status, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Unable to save status file: {e}")

    def get_repo_id(self, repo_info: Dict[str, str]) -> str:
        """Generate unique identifier for repository+commit"""
        key = f"{repo_info['clone_url']}#{repo_info['commit_hash']}"
        return hashlib.md5(key.encode()).hexdigest()[:8]

    def is_repo_cloned(self, repo_info: Dict[str, str]) -> bool:
        """Check if repository+commit has been successfully cloned"""
        commit_short = repo_info['commit_hash'][:8]
        repo_dir_name = f"{repo_info['repo_name']}_{commit_short}"
        repo_path = os.path.join(self.projects_dir, repo_dir_name)
        repo_id = self.get_repo_id(repo_info)
        if not os.path.exists(repo_path):
            return False
            
        git_dir = os.path.join(repo_path, '.git')
        if not os.path.exists(git_dir):
            return False
        if repo_id in self.status:
            status_entry = self.status[repo_id]
            if status_entry.get('status') == 'success' and status_entry.get('path') == repo_path:
                return True
        
        return False

    def clone_repository(self, repo_info: Dict[str, str]) -> bool:
        """Clone specific commit version of a single repository"""
        repo_name = repo_info['repo_name']
        clone_url = repo_info['clone_url']
        commit_hash = repo_info['commit_hash']
        commit_short = commit_hash[:8]
        repo_dir_name = f"{repo_name}_{commit_short}"
        repo_path = os.path.join(self.projects_dir, repo_dir_name)
        repo_id = self.get_repo_id(repo_info)
        
        try:
            if os.path.exists(repo_path):
                git_dir = os.path.join(repo_path, '.git')
                if not os.path.exists(git_dir):
                    import shutil
                    shutil.rmtree(repo_path)
            os.makedirs(repo_path, exist_ok=True)
            subprocess.run(['git', 'init'], cwd=repo_path, capture_output=True, text=True)
            subprocess.run(['git', 'remote', 'add', 'origin', clone_url], 
                         cwd=repo_path, capture_output=True, text=True)
            cmd = ['git', 'fetch', '--depth', '1', 'origin', commit_hash]
            result = subprocess.run(
                cmd, 
                cwd=repo_path,
                capture_output=True, 
                text=True, 
                timeout=3000
            )
            
            if result.returncode == 0:
                checkout_result = subprocess.run(
                    ['git', 'checkout', commit_hash],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                
                if checkout_result.returncode == 0:
                    self.status[repo_id] = {
                        'repo_name': repo_name,
                        'clone_url': clone_url,
                        'commit_hash': commit_hash,
                        'path': repo_path,
                        'status': 'success',
                        'timestamp': time.time(),
                        'size_mb': self.get_repo_size(repo_path)
                    }
                    self.save_status()
                    return True
                else:
                    error_msg = f"Checkout failed: {checkout_result.stderr}"
                    self.status[repo_id] = {
                        'repo_name': repo_name,
                        'clone_url': clone_url,
                        'commit_hash': commit_hash,
                        'path': repo_path,
                        'status': 'failed',
                        'error': error_msg,
                        'timestamp': time.time()
                    }
                    self.save_status()
                    return False
            else:
                error_msg = f"Fetch failed: {result.stderr.strip()}"
                self.status[repo_id] = {
                    'repo_name': repo_name,
                    'clone_url': clone_url,
                    'commit_hash': commit_hash,
                    'path': repo_path,
                    'status': 'failed',
                    'timestamp': time.time(),
                    'error': error_msg
                }
                self.save_status()
                return False
                
        except subprocess.TimeoutExpired:
            self.status[repo_id] = {
                'repo_name': repo_name,
                'clone_url': clone_url,
                'commit_hash': commit_hash,
                'path': repo_path,
                'status': 'failed',
                'timestamp': time.time(),
                'error': 'Clone timeout (>5min)'
            }
            self.save_status()
            return False
            
        except Exception as e:
            self.status[repo_id] = {
                'repo_name': repo_name,
                'clone_url': clone_url,
                'commit_hash': commit_hash,
                'path': repo_path,
                'status': 'failed',
                'timestamp': time.time(),
                'error': str(e)
            }
            self.save_status()
            return False

    def get_repo_size(self, repo_path: str) -> float:
        """Get repository size (MB)"""
        try:
            result = subprocess.run(
                ['du', '-sm', repo_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return float(result.stdout.split()[0])
        except:
            pass
        return 0.0

    def extract_unique_repositories(self, jsonl_file: str) -> List[Dict[str, str]]:
        """Extract unique repository list from JSONL file"""
        unique_repos = {}
        parse_errors = 0
        
        print("🔍 Analyzing repositories in dataset...")
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_no, line in enumerate(tqdm(lines, desc="Parsing URLs"), 1):
            try:
                data = json.loads(line)
                commit_url = data.get('commit_url')
                
                if commit_url:
                    repo_info = self.parser.parse_url(commit_url)
                    if repo_info:
                        repo_key = f"{repo_info['clone_url']}#{repo_info['commit_hash']}"
                        if repo_key not in unique_repos:
                            unique_repos[repo_key] = repo_info
                    else:
                        parse_errors += 1
                        
            except json.JSONDecodeError:
                parse_errors += 1
                continue
        
        print(f"✅ Found {len(unique_repos)} unique repository+commit combinations")
        if parse_errors > 0:
            print(f"⚠️  {parse_errors} URLs failed to parse")
            
        return list(unique_repos.values())

    def batch_clone(self, repo_list: List[Dict[str, str]], force_reclone: bool = False) -> None:
        """Batch clone repositories"""
        self.stats['total_repos'] = len(repo_list)
        
        print(f"\n🚀 Starting batch clone of {len(repo_list)} repositories")
        print(f"📁 Target directory: {self.projects_dir}")
        print(f"💾 Status file: {self.status_file}")
        
        if not force_reclone:
            print("🔄 Checking existing repositories...")
        pbar = tqdm(repo_list, desc="Cloning repositories", unit="repo")
        
        for repo_info in pbar:
            repo_name = repo_info['repo_name']
            pbar.set_description(f"Processing: {repo_name}")
            if not force_reclone and self.is_repo_cloned(repo_info):
                self.stats['already_cloned'] += 1
                pbar.set_postfix({
                    'Existing': self.stats['already_cloned'],
                    'New': self.stats['newly_cloned'],
                    'Failed': self.stats['failed']
                })
                continue
            success = self.clone_repository(repo_info)
            
            if success:
                self.stats['newly_cloned'] += 1
                pbar.write(f"✅ {repo_name}")
            else:
                self.stats['failed'] += 1
                pbar.write(f"❌ {repo_name}")
            pbar.set_postfix({
                'Existing': self.stats['already_cloned'],
                'New': self.stats['newly_cloned'],
                'Failed': self.stats['failed']
            })
            time.sleep(0.5)

    def print_summary(self):
        """Print statistics summary"""
        print("\n" + "="*60)
        print("📊 Clone Statistics Summary")
        print("="*60)
        print(f"Total repositories: {self.stats['total_repos']}")
        print(f"Already cloned: {self.stats['already_cloned']}")
        print(f"Newly cloned: {self.stats['newly_cloned']}")
        print(f"Clone failed: {self.stats['failed']}")
        
        success_rate = (self.stats['already_cloned'] + self.stats['newly_cloned']) / self.stats['total_repos'] * 100
        print(f"Success rate: {success_rate:.1f}%")
        total_size = 0
        for repo_id, info in self.status.items():
            if info.get('status') == 'success':
                total_size += info.get('size_mb', 0)
        
        if total_size > 1024:
            print(f"Total disk usage: {total_size/1024:.1f} GB")
        else:
            print(f"Total disk usage: {total_size:.0f} MB")

    def print_failed_repos(self):
        """Print failed repositories"""
        failed_repos = []
        for repo_id, info in self.status.items():
            if info.get('status') == 'failed':
                failed_repos.append(info)
        
        if failed_repos:
            print(f"\n❌ Failed repositories ({len(failed_repos)}):")
            for info in failed_repos:
                print(f"  - {info['repo_name']}: {info.get('error', 'Unknown error')}")

    def cleanup_failed_repos(self):
        """Clean up failed repository directories"""
        cleaned = 0
        for repo_id, info in self.status.items():
            if info.get('status') == 'failed':
                repo_path = info.get('path')
                if repo_path and os.path.exists(repo_path):
                    try:
                        import shutil
                        shutil.rmtree(repo_path)
                        cleaned += 1
                    except Exception as e:
                        print(f"⚠️  Cleanup failed: {repo_path} - {e}")
        
        if cleaned > 0:
            print(f"🧹 Cleaned up {cleaned} failed repository directories")


def main():
    parser = argparse.ArgumentParser(description='Batch clone PrimeVul dataset repositories')
    parser.add_argument('--input', '-i',
                       default='primevul_test_paired.jsonl',
                       help='Input JSONL file path')
    parser.add_argument('--projects-dir', '-p',
                       default='../projects',
                       help='Repository clone directory')
    parser.add_argument('--status-file', '-s',
                       default='./clone_status.json',
                       help='Status record file')
    parser.add_argument('--force-reclone', '-f',
                       action='store_true',
                       help='Force re-clone all repositories')
    parser.add_argument('--show-failed', 
                       action='store_true',
                       help='Show failed repository list')
    parser.add_argument('--cleanup-failed',
                       action='store_true', 
                       help='Clean up failed repository directories')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Only analyze, do not execute clone')
    
    args = parser.parse_args()
    cloner = BatchRepositoryCloner(
        projects_dir=args.projects_dir,
        status_file=args.status_file
    )
    if args.show_failed:
        cloner.print_failed_repos()
        return
        
    if args.cleanup_failed:
        cloner.cleanup_failed_repos()
        return
    if not os.path.exists(args.input):
        print(f"❌ Input file does not exist: {args.input}")
        return
        
    repo_list = cloner.extract_unique_repositories(args.input)
    
    if args.dry_run:
        print(f"\n🔍 Dry run mode - analysis only")
        print(f"Found {len(repo_list)} unique repositories:")
        for i, repo in enumerate(repo_list[:10], 1):
            print(f"  {i}. {repo['repo_name']} ({repo['clone_url']})")
        if len(repo_list) > 10:
            print(f"  ... and {len(repo_list) - 10} more repositories")
        return
    cloner.batch_clone(repo_list, force_reclone=args.force_reclone)
    cloner.print_summary()
    cloner.print_failed_repos()
    
    print(f"\n💾 Status saved to: {args.status_file}")
    print("💡 Use --show-failed to view failed repositories")
    print("💡 Use --cleanup-failed to clean up failed directories")


if __name__ == "__main__":
    main()