
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime


class ProgressTracker:
    
    def __init__(self):
        self.stages = {}
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def start_stage(self, stage_name: str, total_items: int, description: str = ""):
        with self.lock:
            self.stages[stage_name] = {
                'total_items': total_items,
                'completed_items': 0,
                'failed_items': 0,
                'description': description,
                'start_time': time.time(),
                'end_time': None,
                'status': 'running'
            }
        
        print(f"🚀 Starting stage: {stage_name}")
        if description:
            print(f"   Description: {description}")
        print(f"   Total items: {total_items}")
    
    def update_progress(self, stage_name: str, completed: int = None, failed: int = None):
        with self.lock:
            if stage_name not in self.stages:
                return
            
            stage = self.stages[stage_name]
            
            if completed is not None:
                stage['completed_items'] = completed
            else:
                stage['completed_items'] += 1
            
            if failed is not None:
                stage['failed_items'] = failed
            
            total = stage['total_items']
            completed_count = stage['completed_items']
            failed_count = stage['failed_items']
            processed = completed_count + failed_count
            
            if processed >= total:
                stage['status'] = 'completed'
                stage['end_time'] = time.time()
            
            progress_percent = (processed / total * 100) if total > 0 else 0
            success_rate = (completed_count / processed * 100) if processed > 0 else 0
            
            elapsed_time = time.time() - stage['start_time']
            if processed > 0:
                avg_time_per_item = elapsed_time / processed
                remaining_items = total - processed
                eta = remaining_items * avg_time_per_item
            else:
                eta = 0
            
            print(f"\r📊 {stage_name}: {processed}/{total} ({progress_percent:.1f}%) "
                  f"Success rate: {success_rate:.1f}% ETA: {eta:.0f}s", end="", flush=True)
            
            if stage['status'] == 'completed':
                print(f"\n✅ Stage completed: {stage_name}")
                print(f"   Total time elapsed: {elapsed_time:.1f}s")
                print(f"   Successful: {completed_count}, Failed: {failed_count}")
    
    def finish_stage(self, stage_name: str):
        with self.lock:
            if stage_name in self.stages:
                stage = self.stages[stage_name]
                stage['status'] = 'completed'
                stage['end_time'] = time.time()
                
                elapsed_time = stage['end_time'] - stage['start_time']
                completed = stage['completed_items']
                failed = stage['failed_items']
                
                print(f"\n✅ Stage completed: {stage_name}")
                print(f"   Total time elapsed: {elapsed_time:.1f}s")
                print(f"   Successful: {completed}, Failed: {failed}")
    
    def get_stage_status(self, stage_name: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            return self.stages.get(stage_name, {}).copy()
    
    def get_overall_status(self) -> Dict[str, Any]:
        with self.lock:
            total_elapsed = time.time() - self.start_time
            
            status = {
                'total_elapsed': total_elapsed,
                'total_stages': len(self.stages),
                'completed_stages': len([s for s in self.stages.values() if s['status'] == 'completed']),
                'running_stages': len([s for s in self.stages.values() if s['status'] == 'running']),
                'stages': {}
            }
            
            for name, stage in self.stages.items():
                stage_copy = stage.copy()
                if stage_copy['end_time']:
                    stage_copy['duration'] = stage_copy['end_time'] - stage_copy['start_time']
                else:
                    stage_copy['duration'] = time.time() - stage_copy['start_time']
                
                status['stages'][name] = stage_copy
            
            return status
    
    def print_summary(self):
        status = self.get_overall_status()
        
        print("\n" + "=" * 50)
        print("📊 Processing Summary")
        print("=" * 50)
        print(f"Total time elapsed: {status['total_elapsed']:.1f}s")
        print(f"Total stages: {status['total_stages']}")
        print(f"Completed: {status['completed_stages']}")
        print(f"Running: {status['running_stages']}")
        print()
        
        for name, stage in status['stages'].items():
            print(f"Stage: {name}")
            print(f"  Status: {stage['status']}")
            print(f"  Time elapsed: {stage['duration']:.1f}s")
            print(f"  Successful: {stage['completed_items']}")
            print(f"  Failed: {stage['failed_items']}")
            if stage['description']:
                print(f"  Description: {stage['description']}")
            print()
        
        print("=" * 50)