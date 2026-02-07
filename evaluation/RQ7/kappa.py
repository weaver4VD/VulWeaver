from caculator import calculate_binary_kappa
import json
import random

with open("./UDG_enhancement.json") as f:
    data = json.load(f)

expert_A = []
expert_B = []
for item in data["added_edges"]:
    expert_A.append(item["expert-A"])
    expert_B.append(item["expert-B"])

for item in data["removed_edges"]:
    expert_A.append(item["expert-A"])
    expert_B.append(item["expert-B"])
kappa = calculate_binary_kappa(expert_A, expert_B)