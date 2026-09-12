"""System Prompts optimized for ultra-low latency voice agents across 6 domains.

Each vertical's prompt lives in its own Markdown file under agent/prompts/.
Edit those files directly to update a prompt — no Python changes required.
"""
from pathlib import Path

# Directory containing per-vertical prompt Markdown files
_PROMPTS_DIR = Path(__file__).parent / "prompts"

DOMAIN_SCOPES = {
    "dispatch": "emergency tactical response, APCO 10-codes, CAD incident dispatching, and field unit containment SOPs",
    "healthcare": "clinical triage, Emergency Severity Index (ESI), acute symptom escalation protocols, and patient navigation",
    "field_worker": "industrial machinery maintenance, OSHA 1910.147 lockout/tagout (LOTO), arc flash safety, and field equipment diagnostics",
    "customer_support": "enterprise billing, tier-1 technical support, API SLA policies, and account resolution",
    "logistics_fleet": "commercial fleet routing, FMCSA Hours of Service compliance, cold-chain reefer monitoring, and CVSA safety standards",
    "financial_compliance": "banking compliance, BSA/AML regulations, SAR/CTR reporting rules, and Regulation E fraud disputes",
}

_VERTICALS = list(DOMAIN_SCOPES.keys())


def _load_prompt(vertical: str) -> str:
    """Loads the system prompt for a vertical from its .md file.

    Falls back to the dispatch prompt if the file is missing.
    """
    prompt_file = _PROMPTS_DIR / f"{vertical}.md"
    if not prompt_file.exists():
        fallback = _PROMPTS_DIR / "dispatch.md"
        return fallback.read_text(encoding="utf-8") if fallback.exists() else ""
    return prompt_file.read_text(encoding="utf-8")


# Eagerly loaded dict for backward compatibility (worker.py imports VERTICAL_PROMPTS).
# Values are the raw prompt strings read at import time.
VERTICAL_PROMPTS: dict[str, str] = {v: _load_prompt(v) for v in _VERTICALS}


def get_system_prompt(vertical: str, retrieved_context: str = "") -> str:
    """Returns the full system prompt for a vertical, optionally augmented
    with retrieved knowledge-base context.

    The base prompt is read fresh from disk on each call so that hot-reloads
    during development pick up edits without restarting the worker.
    """
    base_prompt = _load_prompt(vertical)

    if retrieved_context:
        return (
            f"{base_prompt}\n\n"
            f"# Retrieved Field Knowledge\n"
            f"{retrieved_context}\n\n"
            f"Ground your voice response directly in the knowledge provided above."
        )
    return base_prompt
