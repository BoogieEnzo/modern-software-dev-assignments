from dataclasses import dataclass
from enum import Enum
import re


class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ActionItem:
    description: str
    priority: Priority
    matched_pattern: str


# Strong indicators - explicit action keywords at start
STRONG_PATTERNS = [
    r"^(todo|to-do|action item|task|action):\s*(.+)",
    r"^[-*]\s*(todo|to-do|action item|task|action):\s*(.+)",
]

# Medium indicators - action words in the line
MEDIUM_PATTERNS = [
    r"\b(need to|must|should|have to|remember to|don't forget|fix|complete|review|check|verify|submit|send|create|update|delete|implement|add|remove)\b",
]

# Weak indicators - exclamation and question patterns
WEAK_PATTERNS = [
    r".+!$",  # Ends with exclamation
    r".+\?$",  # Ends with question mark but suggests action
]

# High priority indicators
HIGH_PRIORITY_PATTERNS = [
    r"\b(urgent|asap|critical|important|high priority|immediately|immediately!\!)",
    r"!!+",  # Multiple exclamation marks
]

# Medium priority indicators
MEDIUM_PRIORITY_PATTERNS = [
    r"\b(should|might|consider|review|check)\b",
]


def _determine_priority(text: str) -> Priority:
    """Determine priority based on keywords and patterns."""
    text_lower = text.lower()

    for pattern in HIGH_PRIORITY_PATTERNS:
        if re.search(pattern, text_lower):
            return Priority.HIGH

    for pattern in MEDIUM_PRIORITY_PATTERNS:
        if re.search(pattern, text_lower):
            return Priority.MEDIUM

    return Priority.LOW


def _match_pattern(text: str, patterns: list) -> tuple[bool, str]:
    """Check if text matches any of the given patterns."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return True, pattern
    return False, ""


def extract_action_items(text: str) -> list[ActionItem]:
    """Extract action items from text with enhanced pattern recognition.

    Returns a list of ActionItem objects with description and priority.
    """
    results: list[ActionItem] = []
    seen: set[str] = set()  # Avoid duplicates

    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip empty lines after stripping
        line_normalized = re.sub(r"^[-*]\s*", "", line).strip()  # Remove list markers

        matched = False
        matched_pattern = ""

        # Try strong patterns first (explicit keywords at start)
        for pattern in STRONG_PATTERNS:
            match = re.match(pattern, line_normalized, re.IGNORECASE)
            if match:
                # Extract the action description
                if len(match.groups()) >= 2:
                    description = match.group(2).strip()
                else:
                    description = match.group(1).strip() if match.group(1) else line_normalized

                if description and description not in seen:
                    seen.add(description)
                    priority = _determine_priority(description)
                    results.append(
                        ActionItem(
                            description=description, priority=priority, matched_pattern="strong"
                        )
                    )
                    matched = True
                    break
                elif description:
                    matched = True
                    break

        if matched:
            continue

        # Try medium patterns (action words in line)
        is_medium_match, pattern = _match_pattern(line_normalized, MEDIUM_PATTERNS)
        if is_medium_match:
            if line_normalized not in seen:
                seen.add(line_normalized)
                priority = _determine_priority(line_normalized)
                results.append(
                    ActionItem(
                        description=line_normalized, priority=priority, matched_pattern="medium"
                    )
                )
            continue

        # Try weak patterns (exclamation/question marks)
        is_weak_match, _ = _match_pattern(line_normalized, WEAK_PATTERNS)
        if is_weak_match:
            if line_normalized not in seen:
                seen.add(line_normalized)
                priority = _determine_priority(line_normalized)
                results.append(
                    ActionItem(
                        description=line_normalized, priority=priority, matched_pattern="weak"
                    )
                )

    return results


def extract_action_items_simple(text: str) -> list[str]:
    """Legacy function for backward compatibility.

    Returns list of strings (descriptions only).
    """
    items = extract_action_items(text)
    return [item.description for item in items]
