The results of efficiency evaluation are provided in two files:

- [efficiency_evaluation_results.json](./efficiency_evaluation_results.json): overall efficiency comparison across approaches (Table 6 in the paper).
- [phase_breakdown_results.json](./phase_breakdown_results.json): phase-level breakdown of VulWeaver's efficiency (Table 7 in the paper).

## Table 6. Overall Efficiency Comparison

| Approach | Time (s) | Token (#) |
| --- | ---: | ---: |
| DeepDFA | 79.85 | - |
| CoT | 137.29 | 3435 |
| LLMxCPG | 136.78 | - |
| VulInstruct | 181.37 | 7665 |
| VulTrial | 234.51 | 11659 |
| VulWeaver | 190.15 | 27642 |

## Table 7. Phase-level Breakdown of VulWeaver's Efficiency

| Phase | Time (s) | Time (%) | Token (#) | Token (%) |
| --- | ---: | ---: | ---: | ---: |
| Unified Dependency Graph Construction | 159.4 | 83.8 | 16474 | 59.6 |
| Holistic Vulnerability Context Extraction | 11.8 | 27.5 | 0 | 0.0 |
| Context-Aware LLM Reasoning | 9.4 | 4.4 | 11167 | 40.4 |
| Total | 190.15 | 100.0 | 27642 | 100.0 |