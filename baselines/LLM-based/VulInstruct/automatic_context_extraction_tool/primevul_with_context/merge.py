import json
import os
file_subset = 'primevul_subset_100.json'
file_exclude = 'primevul_full_exclude_100.json'
output_file = 'merged.json'

try:
    with open(file_subset, 'r', encoding='utf-8') as f:
        subset_data = json.load(f)
    with open(file_exclude, 'r', encoding='utf-8') as f:
        exclude_data = json.load(f)
    full_data = subset_data + exclude_data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(full_data, f, indent=2, ensure_ascii=False)


except FileNotFoundError as e:
    print(f"❌ {e}")
except Exception as e:
    print(f"❌ {e}")