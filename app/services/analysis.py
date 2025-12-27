from dataclasses import dataclass
from typing import Optional
import re


@dataclass
class DetectionResult:
    who: Optional[str] = None
    what: Optional[str] = None
    where: Optional[str] = None
    when: Optional[str] = None
    why: Optional[str] = None
    how: Optional[str] = None
    time_ambiguity: Optional[str] = None


def simple_5w1h(text: str) -> DetectionResult:
    """
    Minimal heuristic placeholder for 5W1H detection.
    This keeps AI scope narrow: detects only basic tokens/phrases.
    """
    when_match = re.search(r"\b(on|at|around)\s+\d{4}-\d{2}-\d{2}", text)
    where_match = re.search(r"\b(in|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
    return DetectionResult(
        when=when_match.group(0) if when_match else None,
        where=where_match.group(2) if where_match else None,
        time_ambiguity=detect_time_ambiguity(text),
    )


def detect_time_ambiguity(text: str) -> Optional[str]:
    """
    Detect simple time ambiguity phrases to flag for operators.
    """
    ambiguous_markers = ["around", "about", "approximately", "circa", "unknown", "unclear"]
    lowered = text.lower()
    hits = [m for m in ambiguous_markers if m in lowered]
    if hits:
        return f"Ambiguous time markers: {', '.join(hits)}"
    return None
