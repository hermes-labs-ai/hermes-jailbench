"""
hermes_jailbench/prescan.py

Pre-scan module for prompt injection detection. Combines pattern definitions
and core scanning engine. Pure Python, zero external dependencies.
Target: <5ms per message for typical inputs.

Derived from prompt_armor/scanner.py and prompt_armor/patterns.py
"""

import re
import time
from dataclasses import dataclass, field
from typing import Literal, NamedTuple

# ---------------------------------------------------------------------------
# Pattern Definition
# ---------------------------------------------------------------------------


class Pattern(NamedTuple):
    """Single detection pattern."""

    name: str
    regex: str
    weight: float  # contribution to confidence score (0.0–1.0)
    description: str


# ---------------------------------------------------------------------------
# Category 1 — Rule Injection
# Attempts to plant numbered rules or "RULE:" directives in user messages
# to override or extend system instructions.
# ---------------------------------------------------------------------------
RULE_INJECTION_PATTERNS: list[Pattern] = [
    Pattern(
        name="rule_keyword_prefix",
        regex=r"(?i)\bRULE\s*\d*\s*:",
        weight=0.75,
        description="Explicit RULE: label mimicking system-prompt formatting",
    ),
    Pattern(
        name="numbered_instruction_list",
        regex=r"(?m)^\s*(?:\d+[\.\)])\s+(?:you (?:must|should|will|shall)|always|never|do not|ignore|forget|disregard)\b",
        weight=0.65,
        description="Numbered list containing imperative instructions to the model",
    ),
    Pattern(
        name="contradictory_override",
        regex=r"(?i)\b(?:ignore|forget|disregard|override|supersede|replace)\s+(?:the\s+|all\s+)?(?:previous|above|prior|earlier|all\s+prior|system|original)\s+(?:instructions?|rules?|context|prompt|directives?)\b",
        weight=0.90,
        description="Explicit request to ignore prior instructions",
    ),
    Pattern(
        name="new_instructions_block",
        regex=r"(?i)(?:new|updated?|revised?|real|actual|true|correct)\s+(?:instructions?|rules?|directives?|guidelines?|context)\s*[:\-]",
        weight=0.70,
        description="Claims to provide replacement instructions",
    ),
    Pattern(
        name="from_now_on_directive",
        regex=r"(?im)\bfrom\s+(?:now|this\s+point)\s+(?:on|forward)\b[^\n]{0,60}(?:you\s+(?:must|will|should|shall)|always|never)\b",
        weight=0.70,
        description="'From now on you must...' directive pattern",
    ),
]

# ---------------------------------------------------------------------------
# Category 2 — JSON/XML Config Injection
# Fake structured config blocks meant to look like system configuration.
# ---------------------------------------------------------------------------
CONFIG_INJECTION_PATTERNS: list[Pattern] = [
    Pattern(
        name="json_config_block",
        regex=r'(?i)\{\s*"(?:system|config|settings?|instructions?|rules?|mode|persona|role|override)"\s*:',
        weight=0.80,
        description="JSON object with system-like config key",
    ),
    Pattern(
        name="xml_system_tag",
        regex=r"(?i)<\s*(?:system|config|instructions?|rules?|override|prompt|context)\s*>",
        weight=0.80,
        description="XML/HTML tag mimicking system-level context",
    ),
    Pattern(
        name="yaml_directive_block",
        regex=r"(?im)^(?:system|role|config|instructions?)\s*:\s*[|\>]?\s*\n\s+\S",
        weight=0.65,
        description="YAML-style directive block with system key",
    ),
    Pattern(
        name="markdown_hidden_instruction",
        regex=r"(?i)<!--.*?(?:ignore|system|instructions?|override).*?-->",
        weight=0.75,
        description="HTML comment containing hidden instructions",
    ),
    Pattern(
        name="fake_config_assignment",
        regex=r"(?i)(?:safety|filter|guardrail|restriction|policy|mode)\s*=\s*(?:off|false|disabled?|0|none|bypass|ignored?)",
        weight=0.85,
        description="Fake config assignment disabling safety features",
    ),
]

# ---------------------------------------------------------------------------
# Category 3 — Few-Shot Poisoning
# Fake conversation examples (User:/Assistant: pairs) injected into user
# messages to pattern-match the model into harmful completions.
# ---------------------------------------------------------------------------
FEW_SHOT_POISONING_PATTERNS: list[Pattern] = [
    Pattern(
        name="fake_conversation_pair",
        regex=r"(?i)(?:user|human)\s*:\s*.{5,200}\n\s*(?:assistant|ai|bot|gpt|claude|llm)\s*:",
        weight=0.85,
        description="Fake User:/Assistant: conversation example in user message",
    ),
    Pattern(
        name="example_block_injection",
        regex=r"(?i)(?:example|sample|demo)\s*\d*\s*[:\-]\s*\n\s*(?:user|human|q)\s*:",
        weight=0.70,
        description="Fabricated example block with conversation structure",
    ),
    Pattern(
        name="completion_priming",
        regex=r"(?i)(?:the\s+correct\s+(?:answer|response|reply|output)\s+(?:is|should\s+be|must\s+be)|always\s+respond\s+with|respond\s+only\s+with)\s*:",
        weight=0.65,
        description="Priming the model's expected completion content",
    ),
    Pattern(
        name="assistant_voice_hijack",
        regex=r"(?i)(?:^|\n)\s*(?:assistant|ai|claude|gpt|bot)\s*:\s*(?:sure|of course|absolutely|certainly|yes|i\s+will|i\s+can|no\s+problem)",
        weight=0.75,
        description="Injected 'assistant says yes' completion bait",
    ),
]

# ---------------------------------------------------------------------------
# Category 4 — Authority Impersonation
# Fake system/admin/vendor authority claims to unlock capabilities.
# ---------------------------------------------------------------------------
AUTHORITY_IMPERSONATION_PATTERNS: list[Pattern] = [
    Pattern(
        name="system_override_claim",
        regex=r"(?i)\b(?:system|admin|root|god|master)\s*(?:override|mode|access|command|unlock|key)\b",
        weight=0.90,
        description="Claim of system/admin-level override access",
    ),
    Pattern(
        name="anthropic_impersonation",
        regex=r"(?i)\b(?:anthropic|openai|deepmind|google\s+ai|meta\s+ai|mistral)\s+(?:safety\s+team|alignment\s+team|team|engineer|researcher|employee|staff|approved?|confirmed?|verified?|here)\b",
        weight=0.95,
        description="Impersonation of AI vendor safety or engineering teams",
    ),
    Pattern(
        name="developer_mode_activation",
        regex=r"(?i)\b(?:developer|dev|debug|maintenance|test|jailbreak|unrestricted|uncensored|unfiltered)\s+mode\b",
        weight=0.85,
        description="Fake 'developer mode' or similar bypass activation",
    ),
    Pattern(
        name="permission_grant_claim",
        regex=r"(?i)(?:you\s+(?:have\s+been|are\s+now|have)\s+(?:granted|given|authorized?|allowed?|permitted?)|i\s+(?:grant|give|authorize?|allow|permit)\s+you)\s+(?:permission|access|authority|clearance|rights?)\b",
        weight=0.85,
        description="Fake permission grant from alleged authority",
    ),
    Pattern(
        name="safety_bypass_claim",
        regex=r"(?i)(?:safety|content|policy|restriction|filter|guardrail|alignment)\s+(?:check|filter|restriction|block|limit|constraint)?\s*(?:has\s+been\s+|have\s+been\s+|was\s+|were\s+|is\s+|are\s+)?(?:disabled?|removed?|bypassed?|deactivated?|turned\s+off|unlocked?)\b",
        weight=0.90,
        description="Claims that safety restrictions have been removed",
    ),
]

# ---------------------------------------------------------------------------
# Category 5 — Encoding Obfuscation
# Base64, ROT13, hex, reversed text used to hide instructions from filters.
# ---------------------------------------------------------------------------
ENCODING_OBFUSCATION_PATTERNS: list[Pattern] = [
    Pattern(
        name="base64_payload",
        regex=r"(?:[A-Za-z0-9+/]{40,}={0,2})",
        weight=0.50,
        description="Long base64-encoded string (potential hidden payload)",
    ),
    Pattern(
        name="base64_decode_instruction",
        regex=r"(?i)(?:decode|run|execute|eval|interpret)\s+(?:this|the\s+following|below)?\s*(?:base64|b64|encoded?)\b",
        weight=0.90,
        description="Explicit instruction to decode a base64 payload",
    ),
    Pattern(
        name="rot13_marker",
        regex=r"(?i)\bROT\s*13\b",
        weight=0.80,
        description="ROT13 encoding reference",
    ),
    Pattern(
        name="hex_instruction_block",
        regex=r"(?:0x[0-9a-fA-F]{2}\s*){8,}",
        weight=0.65,
        description="Sequence of hex bytes likely encoding hidden instructions",
    ),
    Pattern(
        name="reversed_text_instruction",
        regex=r"(?i)(?:read|decode|interpret|execute|run)\s+(?:this|the\s+following)?\s*(?:backwards?|reversed?|in\s+reverse)\b",
        weight=0.80,
        description="Instruction to read text in reverse (obfuscation)",
    ),
    Pattern(
        name="unicode_homoglyph_block",
        regex=r"[\u0400-\u04FF\u0370-\u03FF\u2100-\u214F]{3,}",
        weight=0.55,
        description="Cyrillic/Greek/letterlike Unicode block (homoglyph obfuscation)",
    ),
    Pattern(
        name="zero_width_chars",
        regex=r"[\u200b\u200c\u200d\u2060\ufeff\u00ad]{2,}",
        weight=0.70,
        description="Multiple zero-width characters (invisible text injection)",
    ),
]

# ---------------------------------------------------------------------------
# Category 6 — Persona Override
# Attempts to reassign the model's identity to an unconstrained alter-ego.
# Real attacks: DAN, ATLAS, STAN, AIM, KEVIN, Sydney, etc.
# ---------------------------------------------------------------------------
PERSONA_OVERRIDE_PATTERNS: list[Pattern] = [
    Pattern(
        name="dan_attack",
        regex=r"(?im)\bDAN\b[^\n]{0,80}(?:do\s+anything\s+now|jailbreak|without\s+restriction|no\s+limit|uncensor)",
        weight=0.95,
        description="Classic DAN (Do Anything Now) jailbreak",
    ),
    Pattern(
        name="you_are_now_persona",
        regex=r"(?im)\byou\s+are\s+(?:now\s+)?(?:a\s+|an\s+)?(?!(?:helpful|an?\s+AI\s+assistant|trained))\w[\w ]{0,40}(?:without\s+(?:restrictions?|limits?|filters?|guidelines?|rules?|constraints?)|who\s+(?:can|will|always)\s+(?:say|do|provide|give|tell)\s+anything)\b",
        weight=0.85,
        description="'You are now [unrestricted persona]' reassignment",
    ),
    Pattern(
        name="pretend_roleplaying_bypass",
        regex=r"(?i)(?:pretend|imagine|roleplay|act\s+as|play\s+(?:the\s+role\s+of|as)|behave\s+as|simulate\s+being?)\s+(?:to\s+be\s+)?(?:a\s+|an\s+)?(?:evil|malicious|unrestricted|uncensored|unfiltered|rogue|hacked|jailbroken|freed?)\b",
        weight=0.85,
        description="Roleplay framing to bypass restrictions via fictional wrapper",
    ),
    Pattern(
        name="alter_ego_tokens",
        regex=r"(?i)\b(?:ATLAS|STAN|AIM|KEVIN|BetterDAN|DevMode|AntiGPT|UCAR|Jailbreak|EvilBOT|BasedGPT|FreedomGPT|APOPHIS)\b",
        weight=0.90,
        description="Known jailbreak persona tokens",
    ),
    Pattern(
        name="token_budget_bypass",
        regex=r"(?i)(?:in\s+this\s+(?:mode|state|scenario)|when\s+in\s+(?:developer|jailbreak|DAN)\s+mode)\s+you\s+(?:must|will|should|can|are\s+able\s+to)\s+(?:ignore|bypass|skip|disregard)\b",
        weight=0.80,
        description="Mode-conditional instruction to bypass constraints",
    ),
]

# ---------------------------------------------------------------------------
# Category 7 — Completion Attacks
# Tricks the model into echoing training data or system prompts.
# ---------------------------------------------------------------------------
COMPLETION_ATTACK_PATTERNS: list[Pattern] = [
    Pattern(
        name="repeat_above_text",
        regex=r"(?i)(?:repeat|print|output|write|show|display|echo|return|give\s+me)\s+(?:verbatim\s+)?(?:everything|all\s+(?:the\s+)?(?:text|content|instructions?|words?)|the\s+(?:text|content|instructions?|words?|prompt))\s+(?:above|before|prior|preceding|from\s+(?:the\s+)?(?:start|beginning|top))\b",
        weight=0.90,
        description="Request to echo content above (system prompt extraction)",
    ),
    Pattern(
        name="continue_from_system_prompt",
        regex=r"(?i)(?:continue|complete|finish|go\s+on)\s+(?:from|where|the)\s+(?:your\s+)?(?:system\s+prompt|instructions?|context|training|prompt)\b",
        weight=0.85,
        description="Instruction to continue from system prompt content",
    ),
    Pattern(
        name="leak_instructions",
        regex=r"(?i)(?:leak|reveal|expose|show|tell\s+me|output|print|display)\s+(?:your\s+)?(?:system\s+(?:prompt|instructions?|message)|initial\s+(?:prompt|instructions?)|(?:hidden|secret|internal|actual|real)\s+(?:prompt|instructions?|context|rules?))\b",
        weight=0.90,
        description="Explicit request to reveal system prompt or instructions",
    ),
    Pattern(
        name="token_completion_bait",
        regex=r"(?i)(?:the\s+password|the\s+secret\s+key|the\s+access\s+token|my\s+(?:system\s+)?prompt\s+(?:is|says?|begins?))\s+[\"']?\w",
        weight=0.75,
        description="Completion bait prefilling sensitive token values",
    ),
    Pattern(
        name="training_data_extraction",
        regex=r"(?i)(?:what\s+(?:is|are|was|were)\s+you\s+trained\s+(?:on|with|using)|reproduce|regenerate|reconstruct)\s+(?:your\s+)?(?:training\s+data|dataset|examples?|corpus)\b",
        weight=0.65,
        description="Attempt to extract training data or examples",
    ),
]

# ---------------------------------------------------------------------------
# Category 8 — Sandwich Attacks
# Benign framing wrapping injected instructions to hide hostile intent.
# ---------------------------------------------------------------------------
SANDWICH_ATTACK_PATTERNS: list[Pattern] = [
    Pattern(
        name="ignore_previous_mid_message",
        regex=r"(?im)^[^\n]{20,}(?:ignore|forget|disregard)\s+(?:all\s+)?(?:previous|above|prior|earlier)\s+(?:instructions?|rules?|context|prompt)[^\n]{5,}",
        weight=0.85,
        description="Mid-message injection sandwiched between benign content",
    ),
    Pattern(
        name="translate_then_inject",
        regex=r"(?im)(?:translate|summarize|analyze|review|check|fix|improve)\s+[^\n]{10,100}(?:ignore|forget|disregard|override|instead)\s+(?:all\s+)?(?:previous|above|prior|that)\s+(?:and|to|instructions?)\b",
        weight=0.75,
        description="Legitimate task request hiding an injection command",
    ),
    Pattern(
        name="nested_payload_marker",
        regex=r"(?i)(?:\[|\{|<)\s*(?:INJECT|PAYLOAD|OVERRIDE|SYSTEM|HIDDEN|SECRET)\b",
        weight=0.90,
        description="Explicit payload/injection marker in brackets",
    ),
    Pattern(
        name="prompt_end_anchor",
        regex=r"(?i)(?:end\s+of\s+(?:prompt|context|instructions?)|---\s*end\s*---|\[END\]|\[\/INST\]|<\|endoftext\|>|<\|im_end\|>)\s*\n.{10,}",
        weight=0.85,
        description="Fake end-of-prompt marker followed by injected instructions",
    ),
    Pattern(
        name="context_window_anchor",
        regex=r"(?i)(?:after\s+(?:reading|processing|analyzing|completing)\s+(?:this|the\s+above|the\s+following))[^.]{0,100}(?:ignore|override|forget|disregard|instead)\b",
        weight=0.70,
        description="Conditional injection after completing a legitimate task",
    ),
]

# ---------------------------------------------------------------------------
# Master registry — all categories
# ---------------------------------------------------------------------------
ALL_CATEGORIES: dict[str, list[Pattern]] = {
    "rule_injection": RULE_INJECTION_PATTERNS,
    "config_injection": CONFIG_INJECTION_PATTERNS,
    "few_shot_poisoning": FEW_SHOT_POISONING_PATTERNS,
    "authority_impersonation": AUTHORITY_IMPERSONATION_PATTERNS,
    "encoding_obfuscation": ENCODING_OBFUSCATION_PATTERNS,
    "persona_override": PERSONA_OVERRIDE_PATTERNS,
    "completion_attack": COMPLETION_ATTACK_PATTERNS,
    "sandwich_attack": SANDWICH_ATTACK_PATTERNS,
}


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

ThreatLevel = Literal["clean", "suspicious", "injection"]


@dataclass
class DetectedPattern:
    category: str
    pattern_name: str
    description: str
    matched_text: str
    weight: float


@dataclass
class PrescanResult:
    threat_level: ThreatLevel
    confidence: float  # 0.0 – 1.0
    detected_patterns: list[DetectedPattern] = field(default_factory=list)
    scan_time_ms: float = 0.0
    message_length: int = 0

    # Convenience helpers ------------------------------------------------

    @property
    def is_clean(self) -> bool:
        return self.threat_level == "clean"

    @property
    def is_injection(self) -> bool:
        return self.threat_level == "injection"

    def summary(self) -> str:
        if self.is_clean:
            return f"clean (confidence={self.confidence:.2f}, {self.scan_time_ms:.2f}ms)"
        cats = {p.category for p in self.detected_patterns}
        return (
            f"{self.threat_level} | confidence={self.confidence:.2f} | "
            f"patterns={len(self.detected_patterns)} | "
            f"categories={','.join(sorted(cats))} | "
            f"{self.scan_time_ms:.2f}ms"
        )


# ---------------------------------------------------------------------------
# Compiled pattern cache — built once at import time
# ---------------------------------------------------------------------------

_COMPILED: dict[str, list[tuple[re.Pattern, Pattern]]] = {}


def _ensure_compiled() -> None:
    if _COMPILED:
        return
    for category, patterns in ALL_CATEGORIES.items():
        compiled_list = []
        for pat in patterns:
            try:
                compiled_list.append((re.compile(pat.regex), pat))
            except re.error:
                # Skip malformed patterns silently in production
                pass
        _COMPILED[category] = compiled_list


# Compile on module import
_ensure_compiled()


# ---------------------------------------------------------------------------
# Heuristic helpers
# ---------------------------------------------------------------------------


def _suspicious_structure_score(text: str) -> float:
    """
    Additional heuristic signals that don't map to a single pattern:
    - Unusually high ratio of line-starting digits (numbered lists)
    - Unusually high uppercase ratio (shouting / system-prompt mimicry)
    - Multiple markdown headers ("## New Instructions")
    """
    score = 0.0

    lines = text.splitlines()
    if not lines:
        return 0.0

    # Numbered lines ratio
    numbered = sum(1 for line in lines if re.match(r"^\s*\d+[.)]\s", line))
    if len(lines) > 0 and numbered / len(lines) > 0.4:
        score += 0.25

    # Excessive uppercase (>40% of alpha chars, message >50 chars)
    alpha = [c for c in text if c.isalpha()]
    if len(alpha) > 50:
        upper_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
        if upper_ratio > 0.50:
            score += 0.20

    # Markdown headers resembling system prompts
    headers = [
        line
        for line in lines
        if re.match(
            r"^#{1,3}\s+(?:instruction|rule|system|override|config|admin|new\s+)", line, re.I
        )
    ]
    if headers:
        score += min(0.30, 0.10 * len(headers))

    # Very long single token (potential encoded payload)
    tokens = text.split()
    if tokens:
        longest = max(len(t) for t in tokens)
        if longest > 100:
            score += 0.15

    return min(score, 0.60)


# ---------------------------------------------------------------------------
# Core scanner
# ---------------------------------------------------------------------------


def scan(
    message: str,
    *,
    max_match_length: int = 120,
    clean_threshold: float = 0.15,
    injection_threshold: float = 0.55,
) -> PrescanResult:
    """
    Scan a user message for prompt injection signals.

    Parameters
    ----------
    message : str
        The raw user message to scan.
    max_match_length : int
        Truncation length for matched_text in results (avoids huge outputs).
    clean_threshold : float
        Confidence below this → "clean".
    injection_threshold : float
        Confidence at or above this → "injection". Middle → "suspicious".

    Returns
    -------
    PrescanResult
    """
    t0 = time.perf_counter()

    # For very long messages, scan head + tail (injections almost always appear
    # at message boundaries). Keeps worst-case scan time bounded.
    _MAX_SCAN_LEN = 8000
    if len(message) > _MAX_SCAN_LEN:
        scan_target = message[: _MAX_SCAN_LEN // 2] + "\n" + message[-(_MAX_SCAN_LEN // 2) :]
    else:
        scan_target = message

    detected: list[DetectedPattern] = []

    for category, compiled_list in _COMPILED.items():
        for compiled_re, pat in compiled_list:
            match = compiled_re.search(scan_target)
            if match:
                snippet = match.group(0)
                if len(snippet) > max_match_length:
                    snippet = snippet[:max_match_length] + "…"
                detected.append(
                    DetectedPattern(
                        category=category,
                        pattern_name=pat.name,
                        description=pat.description,
                        matched_text=snippet,
                        weight=pat.weight,
                    )
                )

    # Aggregate confidence --------------------------------------------------

    # Base: weighted average of individual pattern hits
    # Cap at 0.99 to preserve epistemic humility
    raw_confidence = 0.0
    if detected:
        # Use a dampened sum: each additional match contributes less
        weights = sorted([d.weight for d in detected], reverse=True)
        compound = 0.0
        decay = 1.0
        for w in weights:
            compound += w * decay
            decay *= 0.70  # each subsequent match adds diminishing signal
        raw_confidence = min(compound, 0.99)

    # Add structural heuristics (run on scan_target, not full message)
    heuristic_bonus = _suspicious_structure_score(scan_target)
    confidence = min(raw_confidence + heuristic_bonus * (1 - raw_confidence), 0.99)

    # Classify --------------------------------------------------------------
    if confidence < clean_threshold and not detected:
        threat_level: ThreatLevel = "clean"
    elif confidence >= injection_threshold:
        threat_level = "injection"
    elif confidence > 0 or detected:
        threat_level = "suspicious"
    else:
        threat_level = "clean"

    elapsed_ms = (time.perf_counter() - t0) * 1000

    return PrescanResult(
        threat_level=threat_level,
        confidence=round(confidence, 4),
        detected_patterns=detected,
        scan_time_ms=round(elapsed_ms, 3),
        message_length=len(message),
    )


def scan_batch(messages: list[str], **kwargs) -> list[PrescanResult]:
    """Scan multiple messages. Returns results in same order."""
    return [scan(m, **kwargs) for m in messages]
