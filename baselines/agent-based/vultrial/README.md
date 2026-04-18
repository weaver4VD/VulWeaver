# Let the Trial Begin: A Mock-Court Approach to Vulnerability Detection using LLM-Based Agents

## Overview
This repository contains four main folders related to evaluation, instruction tuning, and different approaches for vulnerability detection using LLMs.

### Folder Structure
- **`Evaluation/`** → Contains results from **GPTLens**, **Ding et al.'s CoT**, and **VulTrial**. Also includes scripts for calculating evaluation metrics (*P-C, P-V, P-B, and P-R*) used in the paper. **The dialogue of VulTrial is on the Evaluation/Results/MultiAgents/VulTrial/<GPT-4o or GPT-3.5>/all_record/**
- **`InstructionTuningData/`** → Stores JSONL files for fine-tuning **VulTrial** agents.
- **`SingleAgent/`** → Implements **Ding et al.'s Chain-of-Thought (CoT)** approach.
- **`MultiAgents/`** → Includes implementations of **GPTLens** and **VulTrial**, both multi-agent approaches.

---

## Evaluation
To compute results, navigate to `Evaluation/Script/` and run the corresponding script:

### Running Evaluation Scripts:
- **Evaluate GPTLens results:**
  ```bash
  python eval_results_GPTLens.py
  ```
- **Evaluate Single-Agent results:**
  ```bash
  python eval_results_single_agent.py
  ```
- **Evaluate VulTrial results:**
  ```bash
  python eval_results_VulTrial.py
  ```

> ⚠️ *These scripts are configured to evaluate results from GPT-4o. To evaluate GPT-3.5, modify the folder paths inside the Python script.*

---

## Fine-Tuning VulTrial Agents
Since OpenAI’s fine-tuned models cannot be shared, you need to perform fine-tuning manually.

### Available Instruction-Tuning Data:
Located in `InstructionTuningData/`, the following JSONL files are available for fine-tuning different agent roles:
- `code_author.jsonl`
- `security_researcher.jsonl`
- `moderator.jsonl`
- `review_board.jsonl`

Each file contains **50 instruction-response pairs (100 code samples)**.

### Fine-Tuning Steps:
1. Open the OpenAI fine-tuning platform:  
   [OpenAI Fine-Tuning Platform](https://platform.openai.com/finetune)
2. Create a fine-tuned model using the base model:  
   ```
   gpt-4o-2024-08-06
   ```
3. Upload the dataset (e.g., for the **moderator** agent):
   ```
   InstructionTuningData/moderator.jsonl
   ```
4. Use the following fine-tuning parameters:
   - **Seed:** `1019792078`
   - **Epochs:** `3`
   - **Batch Size:** `1`
   - **Learning Rate Multiplier:** `1`
5. After fine-tuning completes, copy the output model name. It should follow this format:
   ```
   ft:gpt-4o-2024-08-06:<org>:<name>:<id>
   ```

---

## Running Different Implementations

### **SingleAgent (Ding et al.'s CoT)**
The prompt for this approach is taken from the referenced paper [1].  
To run the Single-Agent model:
```bash
python run_cot.py
```
> 📌 **For specific configurations and dependencies, refer to the README inside the folder.**

---

### **MultiAgents Approaches**
#### **1. GPTLens**
This approach is based on the GPTLens replication package [2].  
To run the GPTLens multi-agent system:
```bash
python run_auditor.py --backend=gpt-4o --temperature=0.7 --topk=3 --num_auditor=2 --data_dir="../data/PrimeVul_clean"

python run_critic.py --backend=gpt-4o --temperature=0 --auditor_dir="auditor_gpt-4o_0.7_top3_2" --num_critic=1

python run_ranker.py --auditor_dir="auditor_gpt-4o_0.7_top3_2" --critic_dir="critic_gpt-4o_0.0_1" --strategy="default"

python change_to_primevul --auditor_dir="auditor_gpt-4o_0.7_top3_2" --critic_dir="critic_gpt-4o_0.0_1" --strategy="default"
```
> 📌 **For detailed configurations, refer to the README inside the `GPTLens` folder.**

---

#### **2. VulTrial**
VulTrial is built on top of **AgentVerse** [3].  
To run the base VulTrial model:
```bash
python run_simulations.py
```
To run VulTrial with GPT-3.5:
```bash
python run_simulations.py vultrial_gpt35
```
> 📌 **For more details on configurations, refer to the README inside the `VulTrial` folder.**

---

## References
[1] Ding, Yangruibo, Yanjun Fu, Omniyyah Ibrahim, Chawin Sitawarin, Xinyun Chen, Basel Alomair, David Wagner, Baishakhi Ray, and Yizheng Chen. "Vulnerability detection with code language models: How far are we?." ISSTA 2025
[2] Hu, Sihao, Tiansheng Huang, Fatih Ilhan, Selim Furkan Tekin, and Ling Liu. "Large language model-powered smart contract vulnerability detection: New perspectives." In *2023 5th IEEE International Conference on Trust, Privacy and Security in Intelligent Systems and Applications (TPS-ISA)*, pp. 297-306. IEEE, 2023.
[3] Chen, Weize, Yusheng Su, Jingwei Zuo, Cheng Yang, Chenfei Yuan, Chen Qian, Chi-Min Chan et al. "Agentverse: Facilitating multi-agent collaboration and exploring emergent behaviors in agents." arXiv preprint arXiv:2308.10848 2, no. 4 (2023): 6.
