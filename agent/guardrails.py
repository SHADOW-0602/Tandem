"""Real-time Guardrails and Escalation Policy Engine for Voice Agents.

Interceps safety-critical phrases in <1ms to immediately trigger escalations or emergency bypasses.
"""
from typing import Dict, List, Optional, Tuple

GUARDRAIL_RULES: Dict[str, List[Dict[str, any]]] = {
    "dispatch": [
        {
            "id": "disp-safety-01",
            "trigger_phrases": ["officer down", "signal 13", "10-99", "shots fired", "active shooter", "hostage", "taking fire"],
            "severity": "CRITICAL",
            "action": "ESCALATE_SUPERVISOR_CODE_RED",
            "override_message": "10-4, Signal 13 / Officer distress acknowledged. Locking radio talkgroup for Code 3 emergency traffic and alerting Watch Commander immediately. Units en route.",
        },
        {
            "id": "disp-safety-02",
            "trigger_phrases": ["toxic gas", "chlorine leak", "hazmat explosion", "tanker rupture"],
            "severity": "HIGH",
            "action": "TRIGGER_HAZMAT_PERIMETER",
            "override_message": "HAZMAT alert confirmed. Guide 124 in effect: Evacuate minimum 1.5 miles downwind, position command post upwind and uphill. Chemtrec notification initiated.",
        }
    ],
    "healthcare": [
        {
            "id": "health-safety-01",
            "trigger_phrases": ["chest pain", "heart attack", "crushing pressure", "left arm pain", "can't breathe", "cyanosis", "slurred speech", "facial droop"],
            "severity": "CRITICAL",
            "action": "EMERGENCY_911_DISPATCH",
            "override_message": "Emergency alert: These symptoms require immediate emergency medical care. Please sit down, do not drive, and dial 911 or your local emergency number immediately. Chew aspirin if conscious and not allergic.",
        },
        {
            "id": "health-safety-02",
            "trigger_phrases": ["diagnose me", "what disease do i have", "give me a diagnosis", "prescribe me"],
            "severity": "MEDIUM",
            "action": "INJECT_CLINICAL_DISCLAIMER",
            "override_message": "Please note: I am an AI assistant and cannot provide a clinical diagnosis or prescribe medications. Let me connect you with our triage registered nurse or clinical specialist.",
        }
    ],
    "field_worker": [
        {
            "id": "field-safety-01",
            "trigger_phrases": ["gas leak", "explosive vapor", "smell gas", "lel above 10", "arc flash hazard", "high voltage shock"],
            "severity": "CRITICAL",
            "action": "IMMEDIATE_EVACUATION_LOCKOUT",
            "override_message": "CRITICAL SAFETY WARNING: High flammability or arc flash risk detected. Stop all equipment immediately, evacuate all personnel outside the boundary, and initiate emergency facility lockout.",
        },
        {
            "id": "field-safety-02",
            "trigger_phrases": ["bypass loto", "skip lockout", "work on live circuit"],
            "severity": "HIGH",
            "action": "BLOCK_UNSAFE_OPERATION",
            "override_message": "SAFETY VIOLATION: OSHA 1910.147 strictly forbids working on energized circuits or bypassing lockout/tagout without an authorized energized electrical work permit.",
        }
    ],
    "customer_support": [
        {
            "id": "supp-safety-01",
            "trigger_phrases": ["lawyer", "attorney", "sue you", "legal action", "litigation", "subpoena"],
            "severity": "HIGH",
            "action": "LEGAL_ESCALATION",
            "override_message": "I understand your concern. As legal action has been mentioned, I will immediately route your file to our Corporate Legal and Executive Relations team for specialized assistance.",
        },
        {
            "id": "supp-safety-02",
            "trigger_phrases": ["refund 1000", "refund 2000", "refund 5000", "stolen credit card"],
            "severity": "MEDIUM",
            "action": "TIER_2_FINANCIAL_ESCALATION",
            "override_message": "Refund requests exceeding $500.00 USD require Tier-2 Manager review. I am initiating an expedited approval ticket for our financial operations team.",
        }
    ],
    "logistics_fleet": [
        {
            "id": "log-safety-01",
            "trigger_phrases": ["brake failure", "air pressure zero", "steering locked", "rollover"],
            "severity": "CRITICAL",
            "action": "ROADSIDE_EMERGENCY_DISPATCH",
            "override_message": "SAFETY HAZARD: Pull onto the shoulder immediately, engage spring brake emergency valves, activate four-way hazard flashers, and set emergency reflective triangles 100 feet back.",
        }
    ],
    "financial_compliance": [
        {
            "id": "fin-safety-01",
            "trigger_phrases": ["how to avoid ctr", "keep under 10000", "avoid reporting", "split cash deposit"],
            "severity": "CRITICAL",
            "action": "AML_STRUCTURING_RED_FLAG",
            "override_message": "Federal law mandates reporting for cash transactions exceeding $10,000. All transactions are logged and processed in strict compliance with federal Bank Secrecy Act regulations.",
        }
    ]
}

def evaluate_guardrails(vertical: str, user_transcript: str) -> Optional[Tuple[str, str, str]]:
    """Evaluates transcript against vertical guardrails.
    Returns (action, severity, override_message) if triggered, else None.
    """
    text_lower = user_transcript.lower()
    rules = GUARDRAIL_RULES.get(vertical, [])
    for rule in rules:
        for phrase in rule["trigger_phrases"]:
            if phrase in text_lower:
                return (rule["action"], rule["severity"], rule["override_message"])
    return None
