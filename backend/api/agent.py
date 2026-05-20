from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.agents import build_crm_graph
from backend.database import get_db
from backend.schemas.agent import ChatRequest, ChatResponse, ExtractRequest, ExtractResponse
from backend.services.llm import LLMClient, get_llm_client

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
def chat_route(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    graph = build_crm_graph(db, llm)
    state = graph.invoke({"user_input": payload.message, "context": payload.context})
    tool_output = state.get("tool_output", {})
    return {
        "action": state.get("action", "log"),
        "response": state.get("response", ""),
        "tool_output": tool_output,
        "extracted_data": state.get("extracted_data", {}),
        "interaction_id": state.get("interaction_id"),
        "error": state.get("error"),
    }


@router.post("/extract", response_model=ExtractResponse)
def extract_route(
    payload: ExtractRequest,
    llm: LLMClient = Depends(get_llm_client),
):
    return {"model": llm.model, "extracted_data": llm.extract_interaction(payload.text)}
