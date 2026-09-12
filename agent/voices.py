"""Voice-Native Personas & Real-Time Backchanneling Engine.

Configures vertical-specific speech pacing, prosody, and sub-100ms micro-acknowledgments
for ultra-responsive conversational flow.
"""
from typing import Dict, List, Optional
import random

# Vertical Voice Personas
# Pacing: faster for tactical dispatch/logistics; calmer and measured for healthcare.
VERTICAL_VOICE_CONFIGS: Dict[str, Dict[str, any]] = {
    "dispatch": {
        "voice_id": "a0e99841-438c-4a64-b679-ae501e7d6091", # Baritone Radio / Direct
        "model_id": "sonic-3",
        "speed": 1.12,
        "emotion": ["urgency:high", "positivity:low"],
        "backchannels": [
            "10-4, copy.",
            "Copy, standby.",
            "Apex CAD acknowledging.",
            "Unit status received.",
        ]
    },
    "healthcare": {
        "voice_id": "79a125e8-cd45-4c13-8a67-188112f4dd22", # British / Warm Empathetic
        "model_id": "sonic-3",
        "speed": 0.96,
        "emotion": ["positivity:high", "calmness:high"],
        "backchannels": [
            "Understood.",
            "I hear you, checking protocol.",
            "One moment, reviewing clinical triage.",
            "Noted, let me guide you.",
        ]
    },
    "field_worker": {
        "voice_id": "694f12bc-c40d-4460-a022-1dae6253d0e3", # Clear Confident
        "model_id": "sonic-3",
        "speed": 1.05,
        "emotion": ["confidence:high"],
        "backchannels": [
            "RigGuard on line.",
            "Copy that.",
            "Checking equipment schematic.",
            "Stand by, pulling LOTO spec.",
        ]
    },
    "customer_support": {
        "voice_id": "248be419-c632-4f23-adf1-5324ed7dbf1d", # Cheerful / Professional
        "model_id": "sonic-3",
        "speed": 1.0,
        "emotion": ["positivity:high"],
        "backchannels": [
            "Got it, looking into that right now.",
            "Understood, checking your account SLA.",
            "One second, verifying policy.",
        ]
    },
    "logistics_fleet": {
        "voice_id": "50d6beb4-80ea-4802-8387-6c948fe84209", # Direct / CB Radio style
        "model_id": "sonic-3",
        "speed": 1.08,
        "emotion": ["confidence:high"],
        "backchannels": [
            "RouteMaster copy.",
            "Checking FMCSA log.",
            "Got your 20, pulling regulations.",
        ]
    },
    "financial_compliance": {
        "voice_id": "b7d50908-b470-42f7-adfe-8644d632de99", # Serious / Executive
        "model_id": "sonic-3",
        "speed": 0.98,
        "emotion": ["neutral:high"],
        "backchannels": [
            "Acknowledging inquiry.",
            "VaultGuard verifying compliance rule.",
            "Checking BSA guidelines.",
        ]
    }
}

def get_voice_config(vertical: str) -> Dict[str, any]:
    """Retrieves Cartesia voice parameters tailored for the operational vertical."""
    return VERTICAL_VOICE_CONFIGS.get(vertical, VERTICAL_VOICE_CONFIGS["dispatch"])

def get_backchannel_phrase(vertical: str, user_text: str) -> Optional[str]:
    """Decides whether to trigger a sub-100ms auditory backchannel while Moss & LLM run.
    Fires for complex queries or queries with >5 words.
    """
    words = user_text.strip().split()
    if len(words) >= 5:
        cfg = get_voice_config(vertical)
        phrases = cfg.get("backchannels", ["Copy that.", "Understood."])
        return random.choice(phrases)
    return None
