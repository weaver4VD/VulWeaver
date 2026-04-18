import json
import os
import difflib
from pathlib import Path
INPUT_PATH = "merged.json"
OUTPUT_DIR = "/path/to/output/directory"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "fixed_merged_matched_detection_results.json")

print(f"🚀 Generating Ground Truth from: {INPUT_PATH}")
try:
    if not os.path.exists(INPUT_PATH):
        if os.path.exists("primevul_train.json"):
            INPUT_PATH = "primevul_train.json"
            print("⚠️ Absolute path not found, using file in current directory.")
        else:
            raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")

    with open(INPUT_PATH, 'r') as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get('data', [])
    print(f"📊 Loaded {len(items)} items.")

except Exception as e:
    print(f"❌ Could not read input file: {e}")
    items = []
results = []
for item in items:
    cve = item.get("cve_id", "Unknown")
    bef = item.get("vulnerableMethods_before", [])
    aft = item.get("vulnerableMethods_after", [])
    code_b = bef[0].get("raw_code", "") if bef else ""
    code_a = aft[0].get("raw_code", "") if aft else ""
    
    if not code_b: 
        continue
    if code_a:
        diff_list = list(difflib.unified_diff(
            code_b.splitlines(keepends=True), 
            code_a.splitlines(keepends=True),
            fromfile='vulnerable',
            tofile='fixed',
            n=3
        ))
        diff = "".join(diff_list)
    else:
        diff = "No fix available (Code After is empty)."
    entry = {
        "cve_id": cve,
        "code_type": "before",
        "ground_truth_info": {
            "cve_description": f"Vulnerability {cve} fixed by:\n{diff[:3000]}",
            "code_diff": diff,
            "commit_message": "Security Fix"
        }
    }
    results.append(entry)
try:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({"results": results}, f, indent=2)

    print(f"✅ Success! Created {OUTPUT_FILE}")
    print(f"   Total entries: {len(results)}")

except Exception as e:
    print(f"❌ Failed to write output: {e}")
