from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from backend.agents.state import CRMState
from backend.services.llm import LLMClient, VALID_ACTIONS
from backend.tools import TOOL_REGISTRY


def build_crm_graph(db: Session, llm: LLMClient):
    graph = StateGraph(CRMState)
    graph.add_node("intent_detection", lambda state: intent_detection_node(state, llm))
    graph.add_node("tool_router", tool_router_node)
    graph.add_node("tool_execution", lambda state: tool_execution_node(state, db, llm))
    graph.add_node("response_generator", lambda state: response_generator_node(state, llm))

    graph.set_entry_point("intent_detection")
    graph.add_edge("intent_detection", "tool_router")
    graph.add_conditional_edges(
        "tool_router",
        route_to_tool,
        {
            "log": "tool_execution",
            "edit": "tool_execution",
            "delete": "tool_execution",
            "search": "tool_execution",
            "followup": "tool_execution",
            "summarize": "tool_execution",
        },
    )
    graph.add_edge("tool_execution", "response_generator")
    graph.add_edge("response_generator", END)
    return graph.compile()


def intent_detection_node(state: CRMState, llm: LLMClient) -> CRMState:
    next_state = dict(state)
    user_input = next_state.get("user_input", "")
    action = next_state.get("action")
    if action not in VALID_ACTIONS:
        next_state["action"] = llm.classify_intent(user_input)
    if not next_state.get("extracted_data"):
        next_state["extracted_data"] = llm.extract_interaction(user_input)
    return next_state


def tool_router_node(state: CRMState) -> CRMState:
    next_state = dict(state)
    if next_state.get("action") not in VALID_ACTIONS:
        next_state["action"] = "log"
    return next_state


def route_to_tool(state: CRMState) -> str:
    action = state.get("action", "log")
    return action if action in VALID_ACTIONS else "log"


def tool_execution_node(state: CRMState, db: Session, llm: LLMClient) -> CRMState:
    next_state = dict(state)
    action = route_to_tool(next_state)
    tool = TOOL_REGISTRY[action]
    output = tool(db, next_state, llm)
    next_state["tool_output"] = output
    if output.get("interaction_id"):
        next_state["interaction_id"] = output["interaction_id"]
    if output.get("error"):
        next_state["error"] = output["error"]
    return next_state


def response_generator_node(state: CRMState, llm: LLMClient) -> CRMState:
    next_state = dict(state)
    next_state["response"] = llm.generate_response(
        next_state.get("action", "log"),
        next_state.get("tool_output", {}),
    )
    return next_state
