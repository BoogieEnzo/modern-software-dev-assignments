from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from ollama import chat
from dotenv import load_dotenv

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False

def extract_action_items(text: str) -> List[str]:
    # First pass: scan line-by-line for things that "look like" action items
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            # Strip leading bullets / numbering (e.g. "- ", "1.") and checkbox markers
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if no explicit action lines found, fall back to sentence-level heuristic
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Second pass: deduplicate while preserving original order (case-insensitive)
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


def _parse_llm_json_array(raw: str) -> list[str]:
    """Best-effort extraction of a JSON array of strings from model output."""
    raw = raw.strip()
    # Try to locate the first [...] block if there is extra text
    start = raw.find("[")
    end = raw.rfind("]")
    if start != -1 and end != -1 and end > start:
        raw = raw[start : end + 1]
    data: Any = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("LLM output is not a JSON array")
    items: list[str] = []
    for item in data:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                items.append(cleaned)
    return items


def extract_action_items_llm(text: str) -> List[str]:
    """LLM-powered action item extraction using an Ollama model.

    Returns a list of action item strings extracted from the input text.
    """
    if not text.strip():
        return []

    system_prompt = (
        "You are an assistant that reads meeting notes or discussion text and extracts clear, "
        "concrete follow-up action items.\n\n"
        "Output format:\n"
        '- Return ONLY a JSON array of strings, e.g. ["Follow up with client", "Write design doc"].\n'
        "- Do not include any commentary, explanation, or keys other than the JSON array itself.\n"
        "- Each string should be one actionable task written in imperative form.\n"
    )

    user_prompt = (
        "Extract all follow-up action items from the following text. "
        "If there are no clear action items, return an empty JSON array [].\n\n"
        "TEXT:\n"
        f"{text}"
    )

    model_name = os.getenv("OLLAMA_ACTION_MODEL", "gemma3:1b")

    response = chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.0},
    )

    raw_output = response.message.content
    try:
        items = _parse_llm_json_array(raw_output)
        # Deduplicate while preserving order, similar to extract_action_items
        seen: set[str] = set()
        unique: list[str] = []
        for item in items:
            lowered = item.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            unique.append(item)
        return unique
    except Exception:
        # Fallback to heuristic extractor if parsing fails
        return extract_action_items(text)
