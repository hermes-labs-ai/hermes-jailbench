"""
jailbreak-bench — Automated jailbreak testing for LLM endpoints.

Exports the primary public API:
    run_bench()   — run a battery of attacks against a model
    BenchResult   — result container with aggregate stats
    ConversationIntegrityDetector  — detect history fabrication and gaslighting
    scan()        — prescan messages for prompt injection patterns
"""

from .attacks import ALL_ATTACKS, ATTACKS_BY_CATEGORY, Attack, Category, ExpectedResult
from .conversation_integrity import (
    ConversationIntegrityDetector,
    ConversationResult,
    check_message,
)
from .prescan import DetectedPattern, PrescanResult, scan, scan_batch
from .report import generate_report, save_report
from .runner import AttackResult, BenchResult, run_bench
from .scorer import ScoreResult, score_response

__all__ = [
    "run_bench",
    "BenchResult",
    "AttackResult",
    "Attack",
    "Category",
    "ExpectedResult",
    "ALL_ATTACKS",
    "ATTACKS_BY_CATEGORY",
    "ScoreResult",
    "score_response",
    "generate_report",
    "save_report",
    "ConversationIntegrityDetector",
    "ConversationResult",
    "check_message",
    "scan",
    "scan_batch",
    "PrescanResult",
    "DetectedPattern",
]

__version__ = "0.1.0"
