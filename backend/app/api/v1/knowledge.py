from fastapi import APIRouter
from app.schemas import KnowledgeSearchRequest, KnowledgeSearchResponse, KnowledgeSearchResult
from app.services.knowledge_rag import search_knowledge
from app.services.groq_service import answer_knowledge_question
from app.core.config import settings

router = APIRouter()


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_agricultural_knowledge(req: KnowledgeSearchRequest):
    results = search_knowledge(req.query, top_k=req.top_k)

    ai_summary = None
    if settings.groq_configured and results:
        ai_summary = await answer_knowledge_question(req.query, results)

    return KnowledgeSearchResponse(
        query=req.query,
        results=[
            KnowledgeSearchResult(
                title=r["title"],
                publisher=r.get("publisher"),
                url=r.get("url"),
                passage=r["passage"],
                relevance_score=r.get("relevance_score"),
            )
            for r in results
        ],
        ai_summary=ai_summary,
        ai_available=settings.groq_configured,
    )
