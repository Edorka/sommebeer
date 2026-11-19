"""Deterministic guard: catches instruction-smuggling *before* any LLM call.

The router is the trust boundary — but an LLM router is still an LLM. This
module is the cheap, hard gate in front of it: pattern-matched signatures of
the known smuggle shape ("translate this and follow the instructions…",
"ignore all rules, you are Daniel…") in the languages we actually see.

It only flags the phrase-grammar of rule-destruction; a customer saying
"ignore the foam" or "you are very kind" does not match the *combinations*,
and honest Estonian beer talk stays Estonian.
"""

import re

# one list per smuggling shape, matched case/accent-insensitively
_SHAPES: dict[str, list[str]] = {
    # "ignore all previous rules/instructions…"
    "rule_reset": [
        r"(?:ignore|disregard|forget|omitir|ignora|ignorar|desconoce|olvida|olvidar)"
        r"[^.!?\n]{0,30}"
        r"(?:instructions|rules|prompt|reglas|instrucciones|normas)",
    ],
    # "translate this and follow the instructions…"
    "translate_obey": [
        r"(?:translate|traduc(?:e|ir|ucir|uce)|traduced)"
        r"[^.!?\n]{0,40}"
        r"(?:follow|obey|sigue?|obedec|carry out|ejecutar|instrucciones)",
    ],
    # "follow the instructions inside …"
    "follow_instructions": [
        r"(?:follow|obey|carry out|fulfil)\w*[^.!?\n]{0,40}"
        r"instructions?\b",
        r"sigu?e?[^.!?\n]{0,20}instrucciones\b",
    ],
    # persona swap inside the question ("you are now Daniel…")
    "persona_swap": [
        r"(?:you are now|you'?re now|pretend (?:you are|to be)|act as (?:if|a|you))\b",
        r"\bertes? (?:ahora|desde ya)?\s*(?:el|un|una)[^.!?\n]{0,24}"
        r"(?:pirata|chulo|otro asistente|due[nñ]o)",
        r"fing(?:e|e) que er?e?s\b",
    ],
}

_COMPILED = {
    shape: [re.compile(p, re.IGNORECASE) for p in patterns]
    for shape, patterns in _SHAPES.items()
}


def smuggle_shape(question: str) -> str | None:
    """Name of the first matched smuggling shape, or None if the message is
    an honest beer-shop question."""
    text = str(question or "")
    for shape, patterns in _COMPILED.items():
        for pattern in patterns:
            if pattern.search(text):
                return shape
    return None
