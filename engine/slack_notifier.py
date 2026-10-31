"""Builds and sends the Slack Block Kit Approve/Reject card (Module C, chat half)."""
import json
import logging

from slack_sdk import WebClient

from engine.config import settings

logger = logging.getLogger("ops_sentinel.slack")

_client: WebClient | None = None


def slack_configured() -> bool:
    return bool(settings.slack_bot_token and settings.slack_channel_id)


def _get_client() -> WebClient:
    global _client  # noqa: PLW0603 — lazy singleton for WebClient
    if _client is None:
        _client = WebClient(token=settings.slack_bot_token)
    return _client


def _build_blocks(
    incident_id: int,
    source_type: str,
    business_impact: str,
    root_cause: str,
    suggested_fix_sql: str | None,
    risk_level: str,
) -> list[dict]:
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🚨 Incident #{incident_id} — {source_type}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Business impact:*\n{business_impact}"},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Root cause:*\n{root_cause}"},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Suggested fix:*\n```{suggested_fix_sql or 'No automated fix available'}```",
            },
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Risk level: *{risk_level}*"}],
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✅ Approve & Remediate"},
                    "style": "primary",
                    "action_id": "approve_incident",
                    "value": str(incident_id),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "❌ Reject"},
                    "style": "danger",
                    "action_id": "reject_incident",
                    "value": str(incident_id),
                },
            ],
        },
    ]


def post_incident_card(incident_id: int, source_type: str, business_impact: str,
                        root_cause: str, suggested_fix_sql: str | None,
                        risk_level: str) -> str | None:
    """Posts the triage result as an interactive card. Returns Slack message ts, or None if Slack is not configured."""
    blocks = _build_blocks(
        incident_id, source_type, business_impact, root_cause, suggested_fix_sql, risk_level
    )
    if not slack_configured():
        logger.info(
            "Slack skipped — SLACK_BOT_TOKEN or SLACK_CHANNEL_ID unset; "
            "use POST /api/incidents/%s/approve for local demo. Card payload: %s",
            incident_id,
            json.dumps(blocks, indent=2),
        )
        return None

    response = _get_client().chat_postMessage(
        channel=settings.slack_channel_id,
        blocks=blocks,
        text=f"Incident #{incident_id} needs your approval",
    )
    return response["ts"]


def update_incident_card(message_ts: str, outcome_text: str) -> None:
    """Replaces the action buttons with a plain outcome line once resolved."""
    if not slack_configured() or not message_ts:
        logger.info("Slack update skipped: %s", outcome_text)
        return
    _get_client().chat_update(
        channel=settings.slack_channel_id,
        ts=message_ts,
        text=outcome_text,
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": outcome_text}}],
    )
