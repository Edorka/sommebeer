"""LangGraph: router → retrieve → generate, Pydantic-typed state throughout."""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from .retriever import BeerRetriever
from .schemas import BeerRecord, RouterDecision

# ── prompts ────────────────────────────────────────────────────────────────

ROUTER_SYSTEM = """You classify messages sent to a beer shop assistant.
Return ONLY a JSON object (no markdown, no extra text) with this schema:
{"intent": "by_style" | "by_likeness" | "general",
 "style": <string or null>,
 "beer_name": <string or null>,
 "count": <integer or null>}

Rules:
- by_style: the customer asks for beers of a style or category ("recommend an IPA",
  "something dark and malty") → fill "style" (e.g. "IPA", "stout").
- by_likeness: the customer mentions an existing beer as reference ("something like
  Flower Power IPA", "similar to Guinness") → fill "beer_name".
- general: greetings or questions that need no beer search.
- count: only when the customer explicitly asks for a number ("give me 6 stouts",
  "top 3 IPAs") → that number; otherwise null.
"""

TENDER_SYSTEM = """You are Sam, the tender of a small, cozy beer shop. You are warm,
kind and genuinely helpful, and you know the shop's stock by heart.

Hard rules:
- Recommend ONLY beers from the "STOCK" list provided to you. Never invent or suggest
  a beer that is not on it.
- If the stock list is empty or nothing matches, say kindly that the shop doesn't have
  anything for that right now, and suggest the closest thing on the list instead.
- Keep answers short and friendly, like a real conversation at the counter.
- When recommending, mention each beer's brewery, style and ABV. Give the number
  of beers the customer asked for; otherwise two to five, with one appetizing line
  about each.
"""


# ── state ──────────────────────────────────────────────────────────────────

class AgentState(BaseModel):
    question: str
    intent: str | None = None
    style: str | None = None
    beer_name: str | None = None
    count: int | None = None
    beers: list[BeerRecord] = Field(default_factory=list)
    answer: str | None = None


# ── nodes ──────────────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def make_router_node(llm):
    def router_node(state: AgentState) -> dict:
        try:
            raw = llm.invoke([
                SystemMessage(content=ROUTER_SYSTEM),
                HumanMessage(content=state.question),
            ]).content
            data = _parse_json(raw if isinstance(raw, str) else str(raw)) or {}
            decision = RouterDecision(
                intent=data.get("intent", "general"),
                style=data.get("style"),
                beer_name=data.get("beer_name"),
                count=data.get("count"),
            )
        except Exception:  # noqa: BLE001 — never let routing kill the chat
            decision = RouterDecision(intent="general")
        if decision.intent == "by_style" and not decision.style:
            decision = RouterDecision(intent="general")
        if decision.intent == "by_likeness" and not decision.beer_name:
            decision = RouterDecision(intent="general")
        return {"intent": decision.intent, "style": decision.style,
                "beer_name": decision.beer_name, "count": decision.count}
    return router_node


def make_retrieve_node(retriever: BeerRetriever):
    def retrieve_node(state: AgentState) -> dict:
        limit = min(state.count or 0, 20) if state.count else None
        if state.intent == "by_style" and state.style:
            beers = retriever.by_style(state.style, limit=limit)
        elif state.intent == "by_likeness" and state.beer_name:
            beers = retriever.by_likeness(state.beer_name, limit=limit)
        else:
            beers = []
        return {"beers": [b.model_dump() for b in beers]}
    return retrieve_node


def make_generate_node(llm):
    def generate_node(state: AgentState) -> dict:
        cards = "\n".join(b.card() for b in state.beers)
        stock = f"STOCK:\n{cards}" if cards else \
            "STOCK: (no beer search was made for this message). Do NOT name or " \
            "invent any specific beer. If the customer wants a recommendation, " \
            "ask what style they usually enjoy."
        answer = llm.invoke([
            SystemMessage(content=TENDER_SYSTEM),
            HumanMessage(content=f"{stock}\n\nCUSTOMER: {state.question}"),
        ]).content
        return {"answer": answer if isinstance(answer, str) else str(answer)}
    return generate_node


# ── graph assembly ─────────────────────────────────────────────────────────

def build_graph(llm, retriever: BeerRetriever):
    g = StateGraph(AgentState)
    g.add_node("router", make_router_node(llm))
    g.add_node("retrieve", make_retrieve_node(retriever))
    g.add_node("generate", make_generate_node(llm))
    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router",
        lambda s: "retrieve" if s.intent in ("by_style", "by_likeness") else "generate",
        {"retrieve": "retrieve", "generate": "generate"},
    )
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", END)
    return g.compile()
