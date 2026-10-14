"""
RAG (Retrieval-Augmented Generation) agricultural knowledge base.
Uses sentence-transformers + FAISS when available, keyword fallback otherwise.
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Built-in knowledge corpus (sourced from public FAO and agricultural guidance) ──
# These are representative passages. Real deployments should add more documents.
KNOWLEDGE_CORPUS: List[Dict[str, Any]] = [
    {
        "title": "FAO Irrigation and Drainage Paper 56 — Crop Evapotranspiration",
        "publisher": "Food and Agriculture Organization of the United Nations",
        "url": "https://www.fao.org/3/x0490e/x0490e00.htm",
        "passage": (
            "The crop coefficient (Kc) integrates differences in evaporation and transpiration "
            "between the cropped surface and the reference grass surface. Under full soil water "
            "conditions, the single crop coefficient Kc ranges from about 0.3 during initial "
            "stages to as high as 1.25 during mid-season for some crops (FAO-56, Allen et al. 1998)."
        ),
    },
    {
        "title": "FAO-56 — Single Crop Coefficient Method",
        "publisher": "Food and Agriculture Organization of the United Nations",
        "url": "https://www.fao.org/3/x0490e/x0490e0b.htm",
        "passage": (
            "ETc = ET0 × Kc, where ETc is crop evapotranspiration, ET0 is reference "
            "evapotranspiration, and Kc is the crop coefficient. Kc values for rice at "
            "mid-season typically range from 1.05 to 1.20. For wheat: initial 0.30, "
            "mid-season 1.15, late 0.40 (FAO-56 Table 12)."
        ),
    },
    {
        "title": "Drip Irrigation — Water Use Efficiency",
        "publisher": "ICRISAT / FAO",
        "url": "https://www.fao.org/3/y3948e/y3948e00.htm",
        "passage": (
            "Drip irrigation delivers water directly to the root zone with application "
            "efficiencies of 85–95%, compared to 60–75% for surface irrigation. "
            "This reduces deep percolation losses and evaporation, making it highly "
            "suitable for water-scarce conditions."
        ),
    },
    {
        "title": "Effective Rainfall in Irrigated Agriculture",
        "publisher": "FAO",
        "url": "https://www.fao.org/3/S2022E/s2022e00.htm",
        "passage": (
            "Effective rainfall is the portion of total rainfall that is stored in the soil "
            "and used by crops. It excludes surface runoff and deep percolation. A conservative "
            "estimate is 70–80% of observed rainfall for medium-textured soils. Heavy rainfall "
            "events on hard or saturated soils may yield less than 50% effective rainfall."
        ),
    },
    {
        "title": "Water Storage Management for Small Farms",
        "publisher": "ICAR — Indian Council of Agricultural Research",
        "url": "https://www.icar.org.in/",
        "passage": (
            "Farm ponds, check dams, and on-farm reservoirs are important water storage "
            "structures for small and marginal farmers. A water budget (storage ÷ daily demand) "
            "helps farmers plan irrigation cycles. When less than 15% of storage remains, "
            "emergency measures such as deficit irrigation or alternate day scheduling should be considered."
        ),
    },
    {
        "title": "Soil Type and Irrigation Scheduling",
        "publisher": "FAO / ICAR",
        "url": "https://www.fao.org/3/r4082e/r4082e05.htm",
        "passage": (
            "Sandy soils have low water-holding capacity (~10–15% by volume) and require "
            "more frequent, lighter irrigations. Clay soils hold more water (~35–45%) but drain slowly "
            "and are prone to waterlogging. Loam soils (~25–30% available water capacity) are "
            "most suitable for most field crops. Soil type significantly affects irrigation scheduling."
        ),
    },
    {
        "title": "Crop Water Requirements in Semi-Arid India",
        "publisher": "ICRISAT",
        "url": "https://www.icrisat.org/",
        "passage": (
            "In semi-arid regions of India, reference evapotranspiration (ET0) typically ranges "
            "from 4 to 8 mm/day during summer and 2 to 4 mm/day during winter. Crop water "
            "requirements vary from about 300 mm (chickpea) to over 1200 mm (sugarcane) per season. "
            "Deficit irrigation — applying 70–80% of full requirement — can maintain acceptable "
            "yields for many crops while conserving water."
        ),
    },
    {
        "title": "Monsoon Rainfall and Irrigation Planning",
        "publisher": "India Meteorological Department (IMD)",
        "url": "https://mausam.imd.gov.in/",
        "passage": (
            "Forecast rainfall with less than 60–70% probability should not be relied upon for "
            "irrigation planning, as forecast uncertainty is high at this range. Only when "
            "probability exceeds 70% and the expected amount is significant relative to crop "
            "demand should irrigation be delayed. Delaying irrigation carries crop stress risk "
            "if the forecast does not verify."
        ),
    },
    {
        "title": "Deficit Irrigation Strategies",
        "publisher": "FAO",
        "url": "https://www.fao.org/3/y3918e/y3918e00.htm",
        "passage": (
            "Deficit irrigation involves applying less water than the full evapotranspiration "
            "requirement. Under water-scarce conditions, deficit irrigation to 60–80% of ETc "
            "can reduce water use by 20–40% with yield reductions of only 5–15% for many crops "
            "if applied during non-critical growth stages. Critical stages (flowering, grain filling) "
            "should receive full irrigation to protect yield."
        ),
    },
    {
        "title": "When to Irrigate: Soil Moisture Indicators",
        "publisher": "FAO",
        "url": "https://www.fao.org/3/s8684e/s8684e08.htm",
        "passage": (
            "Irrigation should begin when the readily available soil moisture (RAM) is depleted. "
            "A practical rule is to irrigate when the soil appears dry at 15–20 cm depth (finger test), "
            "when leaves show slight wilting in the early morning, or when soil moisture falls below "
            "50% of field capacity for sensitive crops. Waiting until severe wilting occurs will "
            "reduce yield."
        ),
    },
]


def keyword_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Simple keyword-based search for demo mode or when embeddings are unavailable."""
    q_words = set(re.sub(r"[^\w\s]", "", query.lower()).split())
    scored = []
    for doc in KNOWLEDGE_CORPUS:
        text = (doc["title"] + " " + doc["passage"]).lower()
        text_words = set(re.sub(r"[^\w\s]", "", text).split())
        overlap = len(q_words & text_words)
        if overlap > 0:
            scored.append((overlap, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, doc in scored[:top_k]:
        results.append({
            "title": doc["title"],
            "publisher": doc.get("publisher"),
            "url": doc.get("url"),
            "passage": doc["passage"],
            "relevance_score": score / max(len(q_words), 1),
        })
    return results


def semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Semantic search using sentence-transformers + FAISS.
    Falls back to keyword search if unavailable.
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer("all-MiniLM-L6-v2")
        corpus_texts = [d["title"] + ". " + d["passage"] for d in KNOWLEDGE_CORPUS]
        corpus_embeddings = model.encode(corpus_texts, convert_to_numpy=True)
        query_embedding = model.encode([query], convert_to_numpy=True)

        # Cosine similarity
        from numpy.linalg import norm
        scores = [
            float(
                (query_embedding[0] @ emb) / (norm(query_embedding[0]) * norm(emb) + 1e-8)
            )
            for emb in corpus_embeddings
        ]
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for idx in top_indices:
            doc = KNOWLEDGE_CORPUS[idx]
            results.append({
                "title": doc["title"],
                "publisher": doc.get("publisher"),
                "url": doc.get("url"),
                "passage": doc["passage"],
                "relevance_score": round(scores[idx], 3),
            })
        return results
    except Exception as exc:
        logger.warning("Semantic search unavailable (%s) — using keyword fallback", exc)
        return keyword_search(query, top_k)


def search_knowledge(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Public search API — tries semantic, falls back to keyword."""
    return semantic_search(query, top_k)


def get_context_passages(
    crop_type: Optional[str] = None,
    growth_stage: Optional[str] = None,
    soil_type: Optional[str] = None,
    irrigation_method: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant passages for a given farm/crop context.
    Used to ground Groq explanations with real agricultural knowledge.
    """
    query_parts = []
    if crop_type:
        query_parts.append(f"{crop_type} crop water requirement irrigation")
    if growth_stage:
        query_parts.append(f"{growth_stage} stage evapotranspiration")
    if soil_type:
        query_parts.append(f"{soil_type} soil water holding capacity irrigation")
    if irrigation_method:
        query_parts.append(f"{irrigation_method} irrigation efficiency water use")

    query = " ".join(query_parts) if query_parts else "irrigation water management"
    return search_knowledge(query, top_k=4)
