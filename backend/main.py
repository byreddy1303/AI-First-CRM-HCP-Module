from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import agent, followups, hcp, interactions
from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI-First CRM HCP Module",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(hcp.router)
app.include_router(agent.router)
app.include_router(followups.router)


@app.get("/api/health")
def health_check():
    from backend.services.llm import get_llm_client
    llm = get_llm_client()
    return {"status": "ok", "model": llm.model}
