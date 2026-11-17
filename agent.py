#!/usr/bin/env python3
"""sommebeer — the beer shop tender. CLI chat.

Usage:
  .venv/bin/python agent.py                      # interactive chat
  .venv/bin/python agent.py -q "recommend an IPA"
"""

from __future__ import annotations

import argparse

from sombeer.config import get_settings
from sombeer.graph import build_graph
from sombeer.llm import get_chat_model
from sombeer.retriever import BeerRetriever, connect
from sombeer.tracing import setup_tracing


def build_agent():
    settings = get_settings()
    setup_tracing(settings.phoenix)
    client = connect(settings.weaviate)
    retriever = BeerRetriever(settings.weaviate, client)
    llm = get_chat_model(settings.llm)
    return build_graph(llm, retriever), settings


def ask(graph, question: str) -> None:
    state = graph.invoke({"question": question}, config={"recursion_limit": 10})
    print(f"\n{state['answer']}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sam, the beer shop tender")
    parser.add_argument("-q", "--question", help="single question; omit for chat mode")
    parser.add_argument("--no-phoenix", action="store_true", help="disable tracing")
    args = parser.parse_args()

    if args.no_phoenix:
        import os
        os.environ["SOMBEER_PHOENIX__ENABLED"] = "false"

    graph, settings = build_agent()
    provider = settings.llm.provider
    print(f"🍺 Sam the beer tender is in — LLM: {provider}, "
          f"Weaviate: {settings.weaviate.host}:{settings.weaviate.port}/{settings.weaviate.collection}")

    if args.question:
        ask(graph, args.question)
        return

    print("Ask for a beer, or 'quit' to leave. Single-shot answers, no memory.\n")
    while True:
        try:
            question = input("you › ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question or question.lower() in {"quit", "exit", "bye"}:
            break
        ask(graph, question)
    print("cheers! 🍻")


if __name__ == "__main__":
    main()
