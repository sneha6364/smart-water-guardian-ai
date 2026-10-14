"""
Groq AI service — backend-only integration.
Groq is used ONLY for explanations and summarisation.
All numeric calculations are done by the deterministic irrigation engine.
API keys are never logged, printed, or exposed to the frontend.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_client():
    """Return a Groq client only if the API key is configured."""
    if not settings.groq_configured:
        return None
    try:
        from groq import Groq
        return Groq(api_key=settings.GROQ_API_KEY)
    except ImportError:
        logger.error("groq package not installed — run: pip install groq")
        return None
    except Exception as exc:
        logger.error("Failed to initialise Groq client: %s", exc)
        return None


RECOMMENDATION_SYSTEM_PROMPT = """
You are an agricultural assistant helping small farmers in India with water management.
You receive VERIFIED inputs (weather data, farm info, crop info, deterministic calculation results).
Your role is to EXPLAIN the recommendation in simple, practical language — not to calculate new numbers.

Rules:
- Never invent weather observations, rainfall quantities, soil-moisture measurements, crop coefficients,
  water-storage measurements, or scientific sources.
- Use ONLY the numbers and facts given to you in the user message.
- Explain in simple English suitable for a farmer with limited technical background.
- Be honest about uncertainty and missing information.
- If key data is missing, say so clearly.
- Respond ONLY with valid JSON in the exact schema requested.
"""

RECOMMENDATION_SCHEMA = {
    "recommended_action": "string — the primary action the farmer should take",
    "reason": "string — plain-language explanation of why",
    "weather_summary": "string — 1-2 sentence summary of relevant weather",
    "water_budget_summary": "string — 1-2 sentence water storage summary",
    "uncertainty": "string — what is uncertain and why",
    "missing_information": "string — what additional information would improve the recommendation",
    "evidence_sources": "list of {title, publisher, url} — sources supporting the recommendation",
    "next_steps": "string — 2-3 practical next steps for the farmer",
}


async def explain_recommendation(
    farm_info: Dict[str, Any],
    calc_results: Dict[str, Any],
    weather: Dict[str, Any],
    knowledge_passages: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Ask Groq to explain the deterministic recommendation in farmer-friendly language.
    Returns a dict with explanation fields, or a fallback dict if Groq is unavailable.
    """
    client = _get_client()
    if client is None:
        return _demo_explanation(calc_results)

    # Build structured prompt — never pass the raw API key
    user_content = json.dumps({
        "farm_info": farm_info,
        "deterministic_calculation": calc_results,
        "weather_forecast_summary": weather.get("summary", {}),
        "retrieved_knowledge": knowledge_passages[:3],  # top 3 passages only
        "instructions": (
            f"Explain the following recommendation in simple English. "
            f"Use ONLY the numbers in 'deterministic_calculation'. "
            f"Do NOT invent new numbers. "
            f"Return JSON matching this schema: {json.dumps(RECOMMENDATION_SCHEMA)}"
        ),
    }, indent=2)

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=1024,
            timeout=30,
        )
        raw_text = response.choices[0].message.content
        return _parse_groq_response(raw_text, calc_results)

    except Exception as exc:
        # Never expose the key in logs
        safe_msg = str(exc).replace(settings.GROQ_API_KEY, "***") if settings.GROQ_API_KEY else str(exc)
        logger.error("Groq API error: %s", safe_msg)
        return _demo_explanation(calc_results, error=safe_msg)


async def explain_scenario_comparison(
    scenarios: List[Dict[str, Any]],
    farm_info: Dict[str, Any],
) -> str:
    """Ask Groq to compare scenarios in plain language."""
    client = _get_client()
    if client is None:
        return (
            "AI explanation unavailable (Groq not configured). "
            "Review the scenario table above to compare water use and storage impact."
        )

    prompt = (
        f"A farmer has these four irrigation scenarios. "
        f"Compare them briefly in 3-4 plain sentences. "
        f"Highlight the trade-offs between water conservation and crop safety. "
        f"Do NOT invent new numbers — only refer to the figures provided.\n\n"
        f"Farm info: {json.dumps(farm_info, indent=2)}\n"
        f"Scenarios: {json.dumps(scenarios, indent=2)}"
    )
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": RECOMMENDATION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=512,
            timeout=30,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        safe_msg = str(exc).replace(settings.GROQ_API_KEY or "", "***")
        logger.error("Groq scenario comparison error: %s", safe_msg)
        return "AI comparison unavailable. See scenario data above."


async def answer_knowledge_question(
    query: str,
    passages: List[Dict[str, Any]],
) -> str:
    """Use retrieved knowledge passages to answer an agricultural question."""
    client = _get_client()
    if client is None:
        return "AI answer unavailable — Groq not configured. See retrieved passages below."

    passage_text = "\n\n".join(
        f"[Source: {p.get('title', 'Unknown')}]\n{p.get('passage', '')}"
        for p in passages[:5]
    )
    prompt = (
        f"Use ONLY the passages below to answer the farmer's question. "
        f"If the passages do not contain enough information, say so clearly. "
        f"Keep the answer practical and easy to understand.\n\n"
        f"Question: {query}\n\nPassages:\n{passage_text}"
    )
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=512,
            timeout=30,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        safe_msg = str(exc).replace(settings.GROQ_API_KEY or "", "***")
        logger.error("Groq knowledge answer error: %s", safe_msg)
        return "AI answer unavailable. See retrieved passages."


def _parse_groq_response(raw: str, calc_results: Dict) -> Dict[str, Any]:
    """Parse and validate the Groq JSON response. Falls back gracefully."""
    # Strip markdown fences if present
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        parsed = json.loads(text)
        # Validate required fields
        required = ["recommended_action", "reason", "weather_summary",
                    "water_budget_summary", "uncertainty", "next_steps"]
        for key in required:
            if key not in parsed:
                parsed[key] = calc_results.get(key, "Information not available")
        return {**parsed, "ai_available": True}
    except json.JSONDecodeError:
        logger.warning("Groq returned non-JSON — using raw text as reason")
        return {
            "recommended_action": calc_results.get("recommended_action", "See calculation"),
            "reason": raw[:500],
            "weather_summary": "",
            "water_budget_summary": "",
            "uncertainty": "AI response could not be parsed",
            "missing_information": "",
            "evidence_sources": [],
            "next_steps": "",
            "ai_available": True,
        }


def _demo_explanation(calc_results: Dict, error: str = "") -> Dict[str, Any]:
    """Fallback explanation when Groq is unavailable."""
    msg = (
        f"[AI explanation unavailable — {error[:100]}] " if error else
        "[AI explanation unavailable — Groq not configured. Running in demo mode.] "
    )
    return {
        "recommended_action": calc_results.get("recommended_action", "See calculation results"),
        "reason": msg + calc_results.get("reason", ""),
        "weather_summary": "Weather data processed by Open-Meteo. AI summary unavailable.",
        "water_budget_summary": "Water budget calculated deterministically. AI summary unavailable.",
        "uncertainty": calc_results.get("uncertainty", ""),
        "missing_information": ", ".join(calc_results.get("missing_inputs", [])),
        "evidence_sources": [],
        "next_steps": "Review the calculation results above for irrigation guidance.",
        "ai_available": False,
    }
