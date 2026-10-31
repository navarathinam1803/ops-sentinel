# Ops Sentinel — 3-minute demo script (ExaThon)

Target length: **≤ 3:00**. Record screen + voice; show Slack and dashboard where possible.

## Opening (0:00–0:25) — Problem (no-tech statement)

Read or paraphrase the mandated problem statement:

> A platform engineering lead cannot scale business operations efficiently because overnight data pipeline failures disrupt company-wide decision trust, while unoptimized query compute costs silently drain the infrastructure budget before engineers can manually triage them.

One line on outcome: **trusted freshness + less cost waste via human-verified automation**.

## Differentiation (0:25–0:45)

- Watchdog tools **observe**; cost tools **bill** — Ops Sentinel **closes the loop** with approve-then-execute remediation.
- **MCP = read-only investigation**; **admin connection = write only after Slack approval**.

## Live demo (0:45–2:30)

| Time | Action | What judges should see |
|------|--------|-------------------------|
| 0:45 | Open Streamlit dashboard | Platform Trust Score + Cloud Efficiency Rating |
| 1:00 | Show Exasol `SENTINEL` tables (MCP or SQL client) | `PIPELINE_LOGS`, `QUERY_METRICS`, `DATA_LINEAGE` |
| 1:15 | Run `python scripts/inject_demo_incident.py` | New FAILED pipeline + cost spike |
| 1:30 | Engine logs / dashboard refresh | Incident → `AWAITING_APPROVAL`, business impact text |
| 1:45 | Slack card (or logged Block Kit if offline) | Approve / Reject buttons, suggested SQL |
| 2:00 | Click **Approve** | Remediation runs; `REMEDIATION_ACTIONS` audit row |
| 2:15 | Dashboard metrics + incident status | Trust/Efficiency update; incident `REMEDIATED` |
| 2:25 | Optional: show **Reject** or guardrail test | Unsafe SQL blocked (`scripts/test_remediation_live.py`) |

## Exasol + MCP slide talking points (2:30–2:50)

1. **Exasol Personal** stores pipeline logs, query cost metrics, and lineage — single analytics layer for reliability + efficiency.
2. **MCP (`exasol-mcp-server`)** lets the triage engine pull error stacks and lineage with a **database-enforced read-only** login.
3. Remediation never uses MCP write tools; writes go through **pyexasol admin** after human approval.

## Close (2:50–3:00)

- Open-source repo (MIT), synthetic data only.
- Repo: `ops-sentinel` — FastAPI engine, Streamlit command center, Slack human-in-the-loop.

## Slide deck checklist

- [ ] 6-step architecture diagram (from README)
- [ ] Module A/B/C table mapping
- [ ] Dedicated **Exasol Personal** + **MCP** slide
- [ ] Market gap: observability vs cost (brief §2)
- [ ] Track 04: “work behind the work” — overnight failures and silent spend

## Pre-demo checklist

- [ ] `exakit status` healthy; schema + seed applied
- [ ] `.env` filled (admin, MCP read-only, LLM, Slack)
- [ ] `uvicorn engine.main:app --port 8000` + `streamlit run dashboard/app.py`
- [ ] ngrok → Slack interactivity URL
- [ ] Bot invited to demo channel
