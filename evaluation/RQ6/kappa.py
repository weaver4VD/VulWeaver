
from caculator import calculate_binary_kappa
import json
import random


with open("./Dual-Annotator-usefulness_GT.json", "r") as f:
    data = json.load(f)
    
expert_A = []
expert_B = []
for item in data:
    expert_A.append(data[item]["expert-A"])
    expert_B.append(data[item]["expert-B"])

kappa = calculate_binary_kappa(expert_A, expert_B)
print(kappa)
