"""
VulInstruct Detection Configuration
Contains API keys, timeouts, and other essential settings for VulInstruct detection system
"""

from pathlib import Path
from typing import List
import os

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = RESULTS_DIR / "logs"
for dir_path in [DATA_DIR, RESULTS_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

OPENAI_API_KEYS = [
    os.getenv("DEEPSEEK_API_KEY")
]

OPENAI_API_BASE = "https://api.deepseek.com"
OPENAI_MODEL = "deepseek-chat"
DEEPSEEK_API_KEYS = OPENAI_API_KEYS
DEEPSEEK_API_BASE = OPENAI_API_BASE
DEEPSEEK_MODEL = OPENAI_MODEL

API_TIMEOUT = 500
REQUEST_DELAY = 1.0
MAX_WORKERS = 4
DETECTION_BATCH_SIZE = 10
DETECTION_RETRY_TIMES = 3
VULSPEC_TOP_K = 10
NVD_TOP_K = 20
NVD_MAX_RESULTS = 100

DEFAULT_DETECTION_MODEL = "deepseek-v3"
DEFAULT_EVALUATION_MODEL = "gpt-5"
DEFAULT_SUMMARY_MODEL = "gpt-3.5-turbo"
DEFAULT_VULSPEC_THRESHOLD = 8
DEFAULT_NVD_THRESHOLD = 8
DEFAULT_SPEC_THRESHOLD = 8
ENABLE_KNOWLEDGE_CACHE = True
CACHE_DIR = PROJECT_ROOT / "cache"
CACHE_DIR.mkdir(exist_ok=True)

EVALUATION_METRICS = [
    "accuracy",
    "precision",
    "recall",
    "f1_score",
    "true_positives",
    "true_negatives",
    "false_positives",
    "false_negatives"
]
CORRECT_EVALUATION_ENABLED = True
STAGE2_EVALUATION_ENABLED = True

import logging

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

__all__ = [
    'OPENAI_API_KEYS', 'OPENAI_API_BASE', 'OPENAI_MODEL', 'DEEPSEEK_API_BASE', 'DEEPSEEK_MODEL',
    'API_TIMEOUT', 'REQUEST_DELAY', 'MAX_WORKERS',
    'DEFAULT_DETECTION_MODEL', 'DEFAULT_EVALUATION_MODEL', 'DEFAULT_SUMMARY_MODEL',
    'DEFAULT_VULSPEC_THRESHOLD', 'DEFAULT_NVD_THRESHOLD', 'DEFAULT_SPEC_THRESHOLD',
    'ENABLE_KNOWLEDGE_CACHE', 'CACHE_DIR',
    'EVALUATION_METRICS', 'CORRECT_EVALUATION_ENABLED',
    'PROJECT_ROOT', 'DATA_DIR', 'RESULTS_DIR', 'LOGS_DIR'
]