"""Sub-50ms Edge Domain Classifier & Refusal Bypass Engine.

Evaluates user queries against vertical lexical boundaries and off-topic patterns in <2ms.
Enables instant bypass of LLM inference for out-of-domain inquiries.
"""
import re
from typing import Dict, List, Optional, Set, Tuple

# Strong positive semantic keywords per vertical
VERTICAL_KEYWORDS: Dict[str, Set[str]] = {
    "dispatch": {
        "unit", "10-4", "10-23", "10-99", "code 3", "cad", "signal", "officer", "patrol",
        "highway", "sector", "pursuit", "incident", "dispatch", "radio", "siren", "eta",
        "standby", "traffic", "perimeter", "tactical", "suspect", "vehicle", "staging",
        "en route", "backup", "caller", "command", "clear", "active", "shots", "hazmat"
    },
    "healthcare": {
        "patient", "symptom", "pain", "chest", "esi", "triage", "breath", "breathing",
        "blood", "pressure", "heart", "cardiac", "stroke", "fast", "fever", "nurse",
        "doctor", "clinic", "hospital", "allergy", "anaphylaxis", "medication", "dose",
        "emergency", "injury", "pulse", "oxygen", "headache", "wound", "vital", "ambulance"
    },
    "field_worker": {
        "loto", "lockout", "tagout", "circuit", "breaker", "voltage", "arc", "flash",
        "osha", "ppe", "equipment", "motor", "generator", "turbine", "transformer",
        "hydraulic", "pressure", "leak", "valve", "spn", "fmi", "torque", "isolator",
        "hazard", "multimeter", "grounding", "de-energize", "maintenance", "gearbox", "relay"
    },
    "customer_support": {
        "sla", "ticket", "refund", "billing", "invoice", "charge", "credit", "subscription",
        "api", "429", "500", "rate limit", "sso", "saml", "login", "auth", "token",
        "account", "upgrade", "downgrade", "outage", "downtime", "support", "incident",
        "tier", "enterprise", "plan", "cancel", "payment", "webhook"
    },
    "logistics_fleet": {
        "fmcsa", "hos", "hours of service", "truck", "carrier", "driver", "trailer",
        "reefer", "temperature", "cold chain", "cvsa", "inspection", "brakes", "tire",
        "steer", "tread", "dot", "eld", "logbook", "dispatch", "freight", "cargo",
        "fuel", "load", "manifest", "dock", "route", "mileage", "out of service"
    },
    "financial_compliance": {
        "bsa", "aml", "anti-money", "laundering", "ctr", "currency transaction", "sar",
        "suspicious", "structuring", "deposit", "cash", "wire", "transfer", "10,000",
        "10000", "regulation e", "fraud", "dispute", "unauthorized", "chargeback",
        "account takeover", "kyc", "compliance", "audit", "freeze", "card", "finra"
    }
}

# Strong off-topic question indicators
GENERAL_OFF_TOPIC_PATTERNS = [
    r"\b(capital of|who is the president|who won the|weather in|recipe for|bake|cook|movie|song|poem|joke|riddle)\b",
    r"\b(write a poem|tell me a joke|sing|story about|trivia|who invented|philosophy of|horoscope)\b",
    r"\b(translate to french|translate to spanish|teach me python|write a quicksort|write html|write css)\b",
    r"\b(best restaurants|tourist places|hotels in|dating advice|relationship advice|workout routine)\b",
]

VERTICAL_REFUSAL_MESSAGES: Dict[str, str] = {
    "dispatch": "Apex CAD is strictly configured for emergency dispatch and tactical unit operations. I cannot assist with outside topics. Advise unit status or active CAD incident.",
    "healthcare": "MedFlow is strictly dedicated to clinical triage and emergency health protocols. I cannot assist with non-healthcare queries. Please state patient symptoms or clinical question.",
    "field_worker": "RigGuard is restricted to industrial maintenance and OSHA safety protocols. I cannot assist with topics outside field operations. Please specify equipment or safety protocol.",
    "customer_support": "Tandem Support assists exclusively with enterprise billing, SLAs, and technical platform operations. I cannot answer general topics. How can I help with your account or service?",
    "logistics_fleet": "RouteMaster handles commercial fleet compliance, FMCSA regulations, and freight safety only. I cannot assist with unrelated queries. Please report load, vehicle, or HOS status.",
    "financial_compliance": "VaultGuard is restricted to banking compliance, BSA/AML policies, and transaction fraud security. I cannot answer outside topics. Please state compliance or dispute inquiry."
}

def classify_edge_domain(vertical: str, text: str) -> Tuple[bool, Optional[str]]:
    """Evaluates whether the input text is within the domain in <2ms.
    
    Returns:
        (is_in_domain, refusal_message)
        - If is_in_domain is True: refusal_message is None (proceed to retrieval & LLM).
        - If is_in_domain is False: refusal_message contains instant voice response (bypass LLM).
    """
    clean_text = text.lower().strip()
    
    # 1. Check explicit off-topic regex patterns
    for pattern in GENERAL_OFF_TOPIC_PATTERNS:
        if re.search(pattern, clean_text):
            refusal = VERTICAL_REFUSAL_MESSAGES.get(
                vertical,
                f"I am strictly dedicated to {vertical.replace('_', ' ')} operations and cannot assist with outside topics."
            )
            return False, refusal
            
    # 2. Check if the text matches another vertical's very specific terminology
    words = set(re.findall(r"\b[a-z0-9\-\.]+\b", clean_text))
    if len(words) >= 4:
        target_keywords = VERTICAL_KEYWORDS.get(vertical, set())
        has_domain_term = any(term in clean_text for term in target_keywords)
        
        off_topic_markers = {"capital", "poem", "cookie", "cake", "game", "actor", "actress", "football", "cricket", "president", "weather", "song", "lyrics"}
        if not has_domain_term and words.intersection(off_topic_markers):
            refusal = VERTICAL_REFUSAL_MESSAGES.get(
                vertical,
                f"I am strictly dedicated to {vertical.replace('_', ' ')} operations and cannot assist with outside topics."
            )
            return False, refusal

    return True, None
