"""Tests for the LangGraph logic: router parsing, fallbacks, prompt building."""

from types import SimpleNamespace

from sommebeer.graph import _parse_json, make_router_node, AgentState


class FakeLLM:
    """Stand-in for a chat model: returns a canned message."""

    def __init__(self, content: str):
        self.content = content
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return SimpleNamespace(content=self.content)


class TestParseJson:
    def test_plain_json(self):
        assert _parse_json('{"a": 1}') == {"a": 1}

    def test_json_in_markdown_fence(self):
        assert _parse_json('```json\n{"intent": "by_style"}\n```') == {
            "intent": "by_style"}

    def test_json_embedded_in_chatter(self):
        assert _parse_json('Sure! {"intent": "general"} hope that helps') == {
            "intent": "general"}

    def test_garbage_returns_none(self):
        assert _parse_json("no json here at all") is None

    def test_broken_json_returns_none(self):
        assert _parse_json('{"intent": ') is None


class TestRouterNode:
    def test_by_style_with_count(self):
        llm = FakeLLM('{"intent": "by_style", "style": "IPA", "count": 6}')
        node = make_router_node(llm)
        out = node(AgentState(question="give me 6 IPAs"))
        assert out["intent"] == "by_style"
        assert out["style"] == "IPA"
        assert out["count"] == 6

    def test_by_likeness(self):
        llm = FakeLLM('{"intent": "by_likeness", "beer_name": "Pliny The Elder"}')
        out = make_router_node(llm)(AgentState(question="like Pliny?"))
        assert out["intent"] == "by_likeness"
        assert out["beer_name"] == "Pliny The Elder"

    def test_garbage_llm_falls_back_to_general(self):
        llm = FakeLLM("I do not understand JSON")
        out = make_router_node(llm)(AgentState(question="hello"))
        assert out["intent"] == "general"

    def test_style_without_intent_becomes_general(self):
        llm = FakeLLM('{"intent": "by_style", "style": null}')
        out = make_router_node(llm)(AgentState(question="beer me"))
        assert out["intent"] == "general"

    def test_likeness_without_beer_becomes_general(self):
        llm = FakeLLM('{"intent": "by_likeness", "beer_name": null}')
        out = make_router_node(llm)(AgentState(question="beer me"))
        assert out["intent"] == "general"
