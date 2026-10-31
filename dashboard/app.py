"""Module C (dashboard half) — the Command Dashboard. Polls the engine's REST
API; keep it dumb on purpose, all logic lives in the engine."""
import os

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_autorefresh import st_autorefresh

load_dotenv()

ENGINE_BASE_URL = os.getenv("ENGINE_BASE_URL", "http://localhost:8000")

st.set_page_config(page_title="Ops Sentinel", page_icon="🛡️", layout="wide")
st.title("🛡️ Ops Sentinel — Platform Command Center")

st_autorefresh(interval=5000, key="ops_sentinel_refresh")


@st.cache_data(ttl=5)
def fetch(path: str) -> dict:
    with httpx.Client(timeout=5) as client:
        return client.get(f"{ENGINE_BASE_URL}{path}").json()


def _status_badge(status: str) -> str:
    colors = {
        "REMEDIATED": "🟢",
        "AWAITING_APPROVAL": "🟡",
        "DETECTED": "🔵",
        "REJECTED": "🔴",
        "FAILED": "⛔",
        "APPROVED": "🟠",
    }
    return f"{colors.get(status, '⚪')} {status}"


col1, col2 = st.columns(2)
try:
    trust = fetch("/api/trust-score")["trust_score"]
    efficiency = fetch("/api/efficiency-score")["efficiency_score"]
    col1.metric("Platform Trust Score", f"{trust}%")
    col2.metric("Cloud Efficiency Rating", f"{efficiency}%")
except httpx.HTTPError:
    st.error("Could not reach the Ops Sentinel engine. Is `uvicorn engine.main:app` running?")
    st.stop()

st.subheader("Recent Incidents")
incidents = fetch("/api/incidents")["incidents"]
if incidents:
    for inc in incidents:
        title = (
            f"#{inc['incident_id']} — {inc['source_type']} — "
            f"{_status_badge(inc.get('status', ''))}"
        )
        with st.expander(title, expanded=inc.get("status") == "AWAITING_APPROVAL"):
            st.markdown(f"**Business impact:** {inc.get('business_impact') or '—'}")
            st.markdown(f"**Root cause:** {inc.get('root_cause') or '—'}")
            st.markdown(f"**Risk:** {inc.get('risk_level') or '—'}")
            fix = inc.get("suggested_fix_sql")
            if fix:
                st.code(fix, language="sql")
            else:
                st.caption("No automated fix suggested.")
            if inc.get("status") == "AWAITING_APPROVAL":
                st.caption(
                    "Approve via Slack, or `curl -X POST "
                    f"{ENGINE_BASE_URL}/api/incidents/{inc['incident_id']}/approve` "
                    "when Slack is not configured."
                )
    df = pd.DataFrame(incidents)
    if "status" in df.columns:
        df["status"] = df["status"].apply(_status_badge)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No incidents yet. Run `python scripts/inject_demo_incident.py` to simulate one.")

st.caption("Auto-refreshes every 5 seconds.")
