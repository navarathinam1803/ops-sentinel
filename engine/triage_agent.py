"""
Module B core: turns raw error/lineage context into a plain-language business
impact narrative and a suggested fix, via whichever LLM provider is configured.
"""
import json
import logging

from engine.config import settings

logger = logging.getLogger("ops_sentinel.triage")

SYSTEM_PROMPT = """You are Ops Sentinel's triage agent for a data platform.
You will be given a pipeline failure's error stack and its downstream data
lineage (which tables and dashboards depend on it). Respond with STRICT JSON
only, matching this schema, no prose outside the JSON:

{
  "business_impact": "<1-3 plain-language sentences a non-engineer exec would understand>",
  "root_cause": "<1-2 sentence technical root cause>",
  "suggested_fix_sql": "<a single SQL statement that would remediate or re-run the pipeline step, or null if no safe automated fix exists>",
  "risk_level": "LOW" | "MEDIUM" | "HIGH"
}

Rules:
- Only suggest SQL you are reasonably confident is safe to re-run.
- If you are not confident, set suggested_fix_sql to null and risk_level to "HIGH".
- Never invent table or column names that were not given to you in the context.
"""


def _build_user_prompt(error_context: dict, lineage: list[dict]) -> str:
    return json.dumps(
        {"incident_context": error_context, "downstream_lineage": lineage},
        default=str,
    )


def llm_configured() -> bool:
    if settings.llm_provider == "anthropic":
        return bool(settings.anthropic_api_key)
    return bool(settings.openai_api_key)


def demo_triage_result(error_context: dict, lineage: list[dict]) -> dict:
    """Deterministic triage when no LLM key is set — same shape as a real response."""
    if error_context.get("QUERY_ID") or error_context.get("ESTIMATED_COST_USD"):
        return {
            "business_impact": (
                "A repeated or unoptimized query is driving compute cost above threshold, "
                "inflating the platform bill without adding business value."
            ),
            "root_cause": (
                "Query metrics show elevated estimated cost"
                + (
                    f" (${error_context.get('ESTIMATED_COST_USD')})"
                    if error_context.get("ESTIMATED_COST_USD")
                    else ""
                )
                + " on a hot table; likely duplicate or missing filter."
            ),
            "suggested_fix_sql": None,
            "risk_level": "HIGH",
        }
    dashboard = "downstream dashboards"
    if lineage:
        dashboard = lineage[0].get("DOWNSTREAM_DASHBOARD") or lineage[0].get("downstream_dashboard") or dashboard
    return {
        "business_impact": (
            f"The {dashboard} may show stale figures because an upstream pipeline step failed."
        ),
        "root_cause": (
            error_context.get("ERROR_STACK")
            or "Pipeline failure recorded in PIPELINE_LOGS; see error stack for transform details."
        )[:500],
        "suggested_fix_sql": "UPDATE sales_clean SET region_code = 'UNKNOWN' WHERE region_code IS NULL",
        "risk_level": "MEDIUM",
    }


def triage(error_context: dict, lineage: list[dict]) -> dict:
    if not llm_configured():
        logger.info("LLM skipped — no API key for provider %s", settings.llm_provider)
        return demo_triage_result(error_context, lineage)

    user_prompt = _build_user_prompt(error_context, lineage)

    if settings.llm_provider == "anthropic":
        return _triage_anthropic(user_prompt)
    return _triage_openai(user_prompt)


def _triage_openai(user_prompt: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return json.loads(response.choices[0].message.content)


def _triage_anthropic(user_prompt: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = message.content[0].text
    return json.loads(text)
