"""Phoenix span annotations — the thumbs of the house land here."""

import httpx

ANNOTATION_NAME = "user_feedback"

RATING_LABELS = {"up": "thumbs_up", "down": "thumbs_down"}
RATING_SCORES = {"up": 1.0, "down": -1.0}


def annotate_span(endpoint: str, span_id: str, trace_id: str, rating: str) -> None:
    """Attach a HUMAN annotation to the request span that produced the answer.

    `identifier` keys the annotation to the conversation turn, so a re-vote
    (thumbs changed) replaces the previous value instead of stacking.
    """
    if not (len(span_id) == 16 and set(span_id) <= set("0123456789abcdef")):
        raise ValueError("span_id must be 16 hex chars")
    payload = {
        "data": [{
            "name": ANNOTATION_NAME,
            "annotator_kind": "HUMAN",
            "identifier": trace_id,
            "span_id": span_id,
            "result": {
                "label": RATING_LABELS[rating],
                "score": RATING_SCORES[rating],
            },
        }],
    }
    url = endpoint.rstrip("/") + "/v1/span_annotations"
    response = httpx.post(url, json=payload, timeout=5)
    response.raise_for_status()
