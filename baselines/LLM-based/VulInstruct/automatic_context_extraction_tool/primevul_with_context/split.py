import json
import random
with open('primevul_zh_format_complete.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

random.seed(42)
shuffled_data = random.sample(data, len(data))
subset_100 = shuffled_data[:100]
exclude_100 = shuffled_data[100:]

with open('primevul_subset_100.json', 'w', encoding='utf-8') as f:
    json.dump(subset_100, f, indent=2, ensure_ascii=False)

with open('primevul_exclude_100.json', 'w', encoding='utf-8') as f:
    json.dump(exclude_100, f, indent=2, ensure_ascii=False)
subset_cves = set(item['cve_id'] for item in subset_100)
exclude_cves = set(item['cve_id'] for item in exclude_100)

with open('subset_100_cve_ids.txt', 'w') as f:
    f.write('\n'.join(sorted(subset_cves)))

with open('exclude_100_cve_ids.txt', 'w') as f:
    f.write('\n'.join(sorted(exclude_cves)))
