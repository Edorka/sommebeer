#!/usr/bin/env python3
"""sommebeer — the beer shop tender. CLI chat.

Usage:
  .venv/bin/python agent.py                      # interactive chat
  .venv/bin/python agent.py -q "recommend an IPA"
"""

from __future__ import annotations

import argparse
import os

from sommebeer.config import get_settings
from sommebeer.graph import build_graph
from sommebeer.llm import get_chat_model
from sommebeer.retriever import BeerRetriever, connect
from sommebeer.tracing import setup_tracing


def build_agent():
    settings = get_settings()
    setup_tracing(settings.phoenix)
    client = connect(settings.weaviate)
    retriever = BeerRetriever(settings.weaviate, client)
    chat_model = get_chat_model(settings.llm)
    return build_graph(chat_model, retriever), settings


def ask(graph, question: str) -> None:
    state = graph.invoke({"question": question}, config={"recursion_limit": 10})
    print(f"\n{state['answer']}\n")


def _parse_args():
    parser = argparse.ArgumentParser(description="Sam, the beer shop tender")
    parser.add_argument("-q", "--question",
                        help="single question; omit for chat mode")
    parser.add_argument("--no-phoenix", action="store_true",
                        help="disable tracing")
    return parser.parse_args()


def _greet(settings) -> None:
    print(f"🍺 Sam the beer tender is in — LLM: {settings.llm.provider}, "
          f"Weaviate: {settings.weaviate.host}:{settings.weaviate.port}/"
          f"{settings.weaviate.collection}")
    print("Ask for a beer, or 'quit' to leave. "
          "Single-shot answers, no memory.\n")


def _chat_loop(graph) -> None:
    while True:
        try:
            question = input("you › ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question or question.lower() in {"quit", "exit", "bye"}:
            break
        ask(graph, question)


def main() -> None:
    args = _parse_args()
    if args.no_phoenix:
        os.environ["SOMMEBEER_PHOENIX__ENABLED"] = "false"
    graph, settings = build_agent()
    _greet(settings)
    if args.question:
        ask(graph, args.question)
        return
    _chat_loop(graph)
    print("cheers! 🍻")


if __name__ == "__main__":
    main()
