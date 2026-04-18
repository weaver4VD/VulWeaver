# PrimeVul Dataset Formatting

This directory contains scripts to convert the [PrimeVul](https://drive.google.com/drive/folders/1cznxGme5o6A_9tT8T47JUh3MPEpRYiKK) raw test set into the format required by VulWeaver.

## Data

- **Source:** Place `primevul_test_paired.jsonl` and `file_info.json` under `primevul_dataset/PrimeVul/` (from the PrimeVul Google Drive).
- **Output:** `primevul_test_formatted.json` (VulWeaver-compatible format).

## Usage

```bash
python format_primevul_dataset.py
```

Then proceed with the evaluation steps described in [../README.md](../README.md).
