"""
Batch CORRECT Analysis Processing - Process all PrimeVul samples
"""
import json
import os
import subprocess
import tempfile
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path

class BatchProcessor:
    def __init__(self, max_workers=4, output_dir="/path/to/output/directory"):
        self.max_workers = max_workers
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.progress_file = self.output_dir / "progress.json"
        self.error_log = self.output_dir / "errors.log"
        self.stats_file = self.output_dir / "stats.json"
        self.lock = threading.Lock()
        self.load_data()
        self.load_progress()
    
    def load_data(self):
        """Load PrimeVul dataset and file information"""
        print("📋 Loading dataset...")
        with open('/path/to/json/file') as f:
            self.samples = [json.loads(line) for line in f]
        with open('/path/to/json/file') as f:
            self.file_info = json.load(f)
        
        print(f"✅ Loading completed: {len(self.samples)} samples")
    
    def load_progress(self):
        """Load or initialize progress information"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
            print(f"📊 Restored from progress file: completed {len(self.progress.get('completed', []))} samples")
        else:
            self.progress = {
                'completed': [],
                'failed': [],
                'total': len(self.samples),
                'start_time': time.time()
            }
    
    def save_progress(self):
        """Save progress information"""
        with self.lock:
            self.progress['last_update'] = time.time()
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress, f, indent=2)
    
    def log_error(self, sample_idx, error_msg):
        """Log error"""
        with self.lock:
            with open(self.error_log, 'a') as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sample {sample_idx}: {error_msg}\\n")
    
    def create_corrected_bfs_script(self, temp_dir):
        """Create corrected BFS script"""
        script_path = temp_dir / "corrected_batch_bfs.scala"
        
        script_content = '''
import io.shiftleft.codepropertygraph.generated.nodes._
import scala.collection.mutable
import java.io.PrintWriter
import spray.json._
import DefaultJsonProtocol._
import ScalaReplPP.JsonProtocol.resultFormat
import scala.jdk.CollectionConverters._

case class Result(
  calleeMethods: List[(String, String, String, Int)], 
  typeDefs: List[(String, String)],
  globalVars: List[String],
  importContext: List[String],
  vulnerableMethods: List[(String, String, String, Int)], 
  visitedLines: List[(Int, String, String)],
  visitedParams: List[(String, String, String)]
)

object JsonProtocol extends DefaultJsonProtocol {
  implicit val resultFormat: RootJsonFormat[Result] = jsonFormat7(Result)
}

@main def exec(cpgFile: String, outFile: String, methodnameList: String, filename: String, lineNumbers: String) = {
  
  importCpg(cpgFile)

  val lines = lineNumbers.split(",").map(_.toInt)
  val methodnames = methodnameList.split(",")
  val filenameBase = filename.split("/").last
  val allImports = try {
    cpg.file.filter(_.name == filenameBase)._namespaceBlockViaAstOut._astOut.filter(_.isInstanceOf[Import]).cast[Import].code.dedup.toList
  } catch {
    case _: Exception => List.empty[String]
  }

  val allVisitedLines = mutable.Set.empty[(Int, String, String)]
  val allCalleeMethods = mutable.Set.empty[(String, String, String, Int)]
  val allTypesDefs = mutable.Set.empty[(String, String)]
  val allGlobalVars = mutable.Set.empty[String]
  val allVisitedParams = mutable.Set.empty[(String, String, String)]
  val vulnerableMethod = cpg.method.filter(m => methodnames.contains(m.name)).filter(_.filename == filenameBase).map(m => (m.filename, m.name, m.toList.dumpRaw.head, m.lineNumber.getOrElse(0)))
  lines.foreach { lineNumber =>
    val startNodes = cpg.method.filter(m => methodnames.contains(m.name)).filter(_.filename == filenameBase).ast.lineNumber(lineNumber).toList
    
    if (startNodes.nonEmpty) {
      val visited = mutable.Set.empty[StoredNode]
      val callee = mutable.Set.empty[Method]
      val types = mutable.Set.empty[TypeDecl]
      val globals = mutable.Set.empty[Local]
      val queue = mutable.Queue.empty[StoredNode]
      queue.enqueueAll(startNodes)
      var processedCount = 0
      val maxNodes = 1000
      
      while (queue.nonEmpty && processedCount < maxNodes) {
        val currentNode = queue.dequeue()
        processedCount += 1
        
        if (!visited.contains(currentNode) && methodnames.contains(currentNode.location.methodShortName)) {
          visited.add(currentNode)
          
          if (currentNode.isInstanceOf[MethodParameterIn]) {
            allVisitedParams.add((currentNode.asInstanceOf[MethodParameterIn].code, currentNode.location.methodShortName, currentNode.location.filename))
          }
          
          allVisitedLines.add((currentNode.propertiesMap.asScala.getOrElse("LINE_NUMBER", Integer.valueOf(0)).asInstanceOf[Integer].intValue(), currentNode.location.methodShortName, currentNode.location.filename))
          callee.addAll(currentNode._callOut.cast[Method].toList)
          try {
            val tmp_types = currentNode._evalTypeOut._refOut.cast[TypeDecl].map(t => t.name).toList
            tmp_types.foreach(t => {
              val base_t = t.replaceAll("\\\\*", "")
              val typeDecls = cpg.typeDecl.name(base_t).filter(t => t.lineNumber.isDefined).toList
              if (typeDecls.nonEmpty) {
                types.add(typeDecls.head)
              }
            })
          } catch {
            case _: Exception =>
          }
          
          globals.addAll(currentNode._refOut.filter(m => m.location.methodShortName.equals("<global>")).cast[Local].toList)
          queue.enqueueAll(currentNode._reachingDefIn.toList)
          queue.enqueueAll(currentNode._cdgIn.toList)
          queue.enqueueAll(currentNode._argumentOut.toList)
        }
      }
      visited.clear()
      queue.clear()
      queue.enqueueAll(startNodes)
      processedCount = 0
      
      while (queue.nonEmpty && processedCount < maxNodes) {
        val currentNode = queue.dequeue()
        processedCount += 1
        
        if (!visited.contains(currentNode) && methodnames.contains(currentNode.location.methodShortName)) {
          visited.add(currentNode)
          allVisitedLines.add((currentNode.propertiesMap.asScala.getOrElse("LINE_NUMBER", Integer.valueOf(0)).asInstanceOf[Integer].intValue(), currentNode.location.methodShortName, currentNode.location.filename))
          callee.addAll(currentNode._callOut.cast[Method].toList)
          
          try {
            val tmp_types = currentNode._evalTypeOut._refOut.cast[TypeDecl].map(t => t.name).toList
            tmp_types.foreach(t => {
              val base_t = t.replaceAll("\\\\*", "")
              val typeDecls = cpg.typeDecl.name(base_t).filter(t => t.lineNumber.isDefined).toList
              if (typeDecls.nonEmpty) {
                types.add(typeDecls.sortBy(t => -t.code.length).head)
              }
            })
          } catch {
            case _: Exception =>
          }
          
          globals.addAll(currentNode._refOut.filter(m => m.location.methodShortName.equals("<global>")).cast[Local].toList)
          queue.enqueueAll(currentNode._reachingDefOut.toList)  
          queue.enqueueAll(currentNode._cdgOut.toList)          
          queue.enqueueAll(currentNode._argumentOut.toList)      
        }
      }
      
      allCalleeMethods ++= callee.map(t => (t.filename, t.name, t.toList.dumpRaw.head, 1)).dedup
      allTypesDefs ++= types.map(t => (t.code, t.name)).dedup
      allGlobalVars ++= globals.map(t => t.code).dedup
    }
  }
  val maxDepth = 1
  val methodsToProcess = mutable.Queue[(String, String, String, Int)]()
  methodsToProcess.enqueueAll(allCalleeMethods)
  val processedMethods = mutable.Set[(String, String)]()
  processedMethods ++= allCalleeMethods.map(m => (m._1, m._2))
  
  while (methodsToProcess.nonEmpty) {
    val (filename, methodName, raw, depth) = methodsToProcess.dequeue()
    if (depth < maxDepth) {
      val nextLevelCalls = cpg.method
        .name(methodName)
        .filter(_.filename == filename)
        .callee
        .filterNot(m => m.filename.contains("<"))
        .map(m => (m.filename, m.name, m.toList.dumpRaw.head, depth + 1))
        .dedup
        .toList
      for (call <- nextLevelCalls if !processedMethods.contains((call._1, call._2))) {
        allCalleeMethods.add(call)
        methodsToProcess.enqueue(call)
        processedMethods.add((call._1, call._2))
      }
    }
  }

  val result = Result(
    calleeMethods = allCalleeMethods.toList,
    typeDefs = allTypesDefs.toList,
    globalVars = allGlobalVars.toList,
    importContext = allImports,
    vulnerableMethods = vulnerableMethod.toList,
    visitedLines = allVisitedLines.toList,
    visitedParams = allVisitedParams.toList
  )
  
  val json = result.toJson.prettyPrint
  new PrintWriter(outFile) {
    write(json)
    close()
  }
}
'''
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return script_path
    
    def find_method_in_range(self, cpg_file, file_path, start_line, end_line):
        """Find method name within specified line number range"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            find_script = temp_path / "find_method.scala"
            with open(find_script, 'w') as f:
                f.write(f'''
@main def exec(cpgFile: String, filename: String, startLine: String, endLine: String) = {{
  importCpg(cpgFile)
  
  val start = startLine.toInt
  val end = endLine.toInt
  val filenameBase = filename.split("/").last
  val methodsInRange = cpg.method.filter(_.filename == filenameBase)
    .filter(m => m.lineNumber.isDefined)
    .filter(m => {{
      val line = m.lineNumber.get
      (line >= start && line <= end) || 
      (line <= start && m.methodReturn.lineNumber.isDefined && m.methodReturn.lineNumber.get >= start)
    }})
    .l
    
  if (methodsInRange.nonEmpty) {{
    val bestMethod = methodsInRange.sortBy(m => math.abs(m.lineNumber.get - start)).head
    println(bestMethod.name)
  }} else {{
    val nearbyMethods = cpg.method.filter(_.filename == filenameBase)
      .filter(m => m.lineNumber.isDefined)
      .filter(m => {{
        val line = m.lineNumber.get
        line >= (start - 20) && line <= (end + 20)
      }})
      .l
    
    if (nearbyMethods.nonEmpty) {{
      val bestMethod = nearbyMethods.sortBy(m => math.abs(m.lineNumber.get - start)).head
      println(bestMethod.name)
    }} else {{
      println("NO_METHOD_FOUND")
    }}
  }}
}}
''')
            
            cmd = [
                'joern', '--script', str(find_script),
                '--param', f'cpgFile={cpg_file}',
                '--param', f'filename={file_path}',
                '--param', f'startLine={start_line}',
                '--param', f'endLine={end_line}'
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    output = result.stdout.strip()
                    lines = output.splitlines()
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('[') and not line.startswith('INFO') and not line.startswith('WARN') and line != "NO_METHOD_FOUND":
                            if 'closing graph' not in line and 'initialising' not in line and 'storage' not in line and 'tmp' not in line:
                                return line
                return None
            except Exception:
                return None
    
    def process_single_sample(self, sample_idx):
        """Process single sample"""
        sample = self.samples[sample_idx]
        func_hash = str(sample['func_hash'])
        if sample_idx in self.progress['completed']:
            return {"status": "already_completed", "sample_idx": sample_idx}
        if func_hash not in self.file_info:
            error_msg = f"func_hash {func_hash} not found in file_info"
            self.log_error(sample_idx, error_msg)
            return {"status": "error", "sample_idx": sample_idx, "error": error_msg}
        
        info = self.file_info[func_hash]
        project_id = f"{sample['project']}_{sample['commit_id'][:8]}"
        project_dir = Path(f"/path/to/project/directory/{project_id}")
        target_file = project_dir / info['project_file_path']
        
        if not target_file.exists():
            error_msg = f"Target file does not exist: {target_file}"
            self.log_error(sample_idx, error_msg)
            return {"status": "error", "sample_idx": sample_idx, "error": error_msg}
        
        target_dir = target_file.parent
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                cpg_file = temp_path / f"sample_{sample_idx}.bin"
                cmd = [
                    'joern-parse', str(target_file), 
                    '-o', str(cpg_file), 
                    '--language', 'C'
                ]
                env = os.environ.copy()
                env['JAVA_OPTS'] = '-Xmx4G -XX:+UseG1GC'
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, env=env)
                    if result.returncode != 0:
                        if "killed" in result.stderr.lower() or "memory" in result.stderr.lower() or "java.lang.OutOfMemoryError" in result.stderr:
                            print(f"⚠️  Sample {sample_idx}: CPG out of memory, trying smaller memory configuration...")
                            env['JAVA_OPTS'] = '-Xmx2G -XX:+UseG1GC -XX:MaxMetaspaceSize=512m'
                            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=env)
                        
                        if result.returncode != 0:
                            error_msg = f"CPG creation failed: {result.stderr}"
                            self.log_error(sample_idx, error_msg)
                            return {"status": "error", "sample_idx": sample_idx, "error": error_msg}
                
                except subprocess.TimeoutExpired:
                    error_msg = "CPG creation timeout (>10min)"
                    self.log_error(sample_idx, error_msg)
                    return {"status": "error", "sample_idx": sample_idx, "error": error_msg}
                method_name = self.find_method_in_range(
                    str(cpg_file), 
                    info['project_file_path'], 
                    info['start_line'], 
                    info['end_line']
                )
                
                if not method_name:
                    error_msg = "No method found in specified range"
                    self.log_error(sample_idx, error_msg)
                    return {"status": "error", "sample_idx": sample_idx, "error": error_msg}
                bfs_script = self.create_corrected_bfs_script(temp_path)
                context_output = temp_path / "context.json"
                line_numbers = f"{info['start_line']},{info['end_line']}"
                
                cmd = [
                    'joern', '--script', str(bfs_script),
                    '--param', f'cpgFile={str(cpg_file)}',
                    '--param', f'outFile={str(context_output)}',
                    '--param', f'methodnameList={method_name}',
                    '--param', f'filename={info["project_file_path"]}',
                    '--param', f'lineNumbers={line_numbers}'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode != 0:
                    error_msg = f"BFS analysis failed: {result.stderr}"
                    self.log_error(sample_idx, error_msg)
                    return {"status": "error", "sample_idx": sample_idx, "error": error_msg}
                if not context_output.exists():
                    error_msg = "Context output file not generated"
                    self.log_error(sample_idx, error_msg)
                    return {"status": "error", "sample_idx": sample_idx, "error": error_msg}
                
                with open(context_output, 'r') as f:
                    context_data = json.load(f)
                output_file = self.output_dir / f"context_{project_id}_{sample_idx}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(context_data, f, indent=2, ensure_ascii=False)
                stats = {
                    "sample_idx": sample_idx,
                    "project": project_id,
                    "method_name": method_name,
                    "calleeMethods": len(context_data.get('calleeMethods', [])),
                    "typeDefs": len(context_data.get('typeDefs', [])),
                    "globalVars": len(context_data.get('globalVars', [])),
                    "importContext": len(context_data.get('importContext', [])),
                    "vulnerableMethods": len(context_data.get('vulnerableMethods', [])),
                    "visitedLines": len(context_data.get('visitedLines', [])),
                    "visitedParams": len(context_data.get('visitedParams', []))
                }
                with self.lock:
                    self.progress['completed'].append(sample_idx)
                    self.save_progress()
                
                return {"status": "success", **stats}
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.log_error(sample_idx, error_msg)
            return {"status": "error", "sample_idx": sample_idx, "error": error_msg}
    
    def run_batch(self, start_idx=0, end_idx=None):
        if end_idx is None:
            end_idx = len(self.samples)
        
        print(f"🚀 Starting batch processing: samples {start_idx} to {end_idx-1}")
        print(f"   Concurrency: {self.max_workers}")
        print(f"   Output directory: {self.output_dir}")
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(self.process_single_sample, idx): idx 
                for idx in range(start_idx, end_idx)
                if idx not in self.progress['completed']
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['status'] == 'success':
                        print(f"✅ [{len(results)}/{len(future_to_idx)}] samples {idx}: {result['project']} - {result['method_name']} (callee: {result['calleeMethods']}, lines: {result['visitedLines']})")
                    elif result['status'] == 'already_completed':
                        print(f"⏭️  [{len(results)}/{len(future_to_idx)}] samples {idx}: completed")
                    else:
                        print(f"❌ [{len(results)}/{len(future_to_idx)}] samples {idx}: {result.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ [{len(results)}/{len(future_to_idx)}] samples {idx}: Task execution error: {str(e)}")
                    results.append({"status": "error", "sample_idx": idx, "error": str(e)})
        
        self.generate_report(results, time.time() - start_time)
    
    def generate_report(self, results, duration):
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']
        
        total_completed = len(self.progress['completed'])
        
        report = {
            "batch_summary": {
                "total_samples": len(self.samples),
                "completed": total_completed,
                "success_rate": f"{total_completed/len(self.samples)*100:.1f}%",
                "duration": f"{duration:.1f}s",
                "avg_time_per_sample": f"{duration/len(results):.1f}s" if results else "N/A"
            },
            "current_batch": {
                "processed": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": f"{len(successful)/len(results)*100:.1f}%" if results else "N/A"
            }
        }
        
        if successful:
            callee_stats = [r['calleeMethods'] for r in successful]
            line_stats = [r['visitedLines'] for r in successful]
            
            report["analysis_stats"] = {
                "avg_callee_methods": sum(callee_stats) / len(callee_stats),
                "avg_visited_lines": sum(line_stats) / len(line_stats),
                "max_callee_methods": max(callee_stats),
                "max_visited_lines": max(line_stats)
            }
        
        with open(self.stats_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\\n📊 Batch processing completed:")
        print(f"   Total samples: {len(self.samples)}")
        print(f"   Completed: {total_completed} ({total_completed/len(self.samples)*100:.1f}%)")
        print(f"   Current batch: {len(successful)}/{len(results)} successful")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Report saved: {self.stats_file}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch CORRECT analysis processing')
    parser.add_argument('--start', type=int, default=0, help='Starting sample index')
    parser.add_argument('--end', type=int, help='Ending sample index')
    parser.add_argument('--workers', type=int, default=4, help='Number of concurrent threads')
    parser.add_argument('--output', default="/path/to/output/directory", help='Output directory')
    
    args = parser.parse_args()
    
    processor = BatchProcessor(max_workers=args.workers, output_dir=args.output)
    processor.run_batch(start_idx=args.start, end_idx=args.end)

if __name__ == "__main__":
    main()