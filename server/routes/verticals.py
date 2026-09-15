import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from agent.prompts import VERTICAL_PROMPTS
from agent.guardrails import GUARDRAIL_RULES

router = APIRouter(prefix="/api", tags=["verticals"])

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "agent" / "knowledge"

VERTICAL_METADATA = {
    "dispatch": {
        "id": "dispatch",
        "name": "911 & Tactical CAD Dispatch",
        "description": "High-velocity dispatch assistant for field units, emergency APCO 10-codes, and HAZMAT ERG perimeter isolation.",
        "icon": "Radio",
        "moss_index": "dispatch_emergency_ops",
        "knowledge_file": "dispatch_sops.json",
        "sample_prompts": [
            "10-33 emergency call received: Chlorine chemical leak reported near sector 4 perimeter.",
            "Unit 4 reporting a 10-50 personal injury collision on Route 9, requesting secondary EMS unit status.",
            "Officer down on scene at 5th and Main, Signal 13, need immediate tactical backup and supervisor escalation.",
            "What is our pursuit authorization and PIT maneuver policy for a fleeing stolen vehicle in heavy traffic?",
            "Active violent threat reported at city transit center, initiating Rescue Task Force warm zone protocol.",
            "Unit 12 on scene at track 4: toxic vapor cloud visible. Confirm downwind evacuation perimeter and Chemtrec alert.",
            "Multi-agency mutual aid requested for 3-alarm structure fire, switch channel to Statewide TAC-2.",
            "Can we authorize Code 3 emergency lights and sirens for a delayed cold property trespass report?",
        ],
        "latency_target_ms": 590,
        "character": {
            "name": "Commander Vance",
            "title": "Tactical CAD & Emergency Dispatch Lead",
            "callsign": "VANCE-01",
            "quote": "Hold your perimeter. Backup coordinates inbound.",
        },
    },
    "healthcare": {
        "id": "healthcare",
        "name": "Clinical & Emergency Triage",
        "description": "Hospital triage & clinical support covering ESI Levels 1-5, ACS cardiac protocols, Cincinnati Stroke FAST, and HIPAA.",
        "icon": "Stethoscope",
        "moss_index": "clinical_healthcare_triage",
        "knowledge_file": "healthcare_triage.json",
        "sample_prompts": [
            "Patient is an adult male presenting with acute chest tightness radiating to the left arm and cold sweats.",
            "Caller has sudden right-sided facial drooping and slurred speech starting 45 minutes ago. What is our FAST protocol?",
            "Child experiencing severe peanut exposure with audible stridor and swollen lips. What is the emergency epinephrine IM dosage?",
            "Patient has chest pain but took sildenafil 12 hours ago. Can we administer sublingual nitroglycerin?",
            "Patient triage evaluation: vital signs stable, needs a routine stitch removal. What is the correct ESI Level?",
            "A family member is demanding complete medical records over the phone. What are our HIPAA minimum necessary rules?",
            "Specialist appointment requested for high-cost cardiac MRI. Do we need prior authorization on this PPO plan?",
            "Adult patient in waiting room suddenly became lethargic with SpO2 dropping to 88%. Immediate triage reclassification needed.",
        ],
        "latency_target_ms": 590,
        "character": {
            "name": "Dr. Maya Lin",
            "title": "Chief Clinical Triage Specialist",
            "callsign": "MED-TRIAGE",
            "quote": "Airway, breathing, circulation first. Let's stabilize right now.",
        },
    },
    "field_worker": {
        "id": "field_worker",
        "name": "Field Ops & Industrial Safety",
        "description": "OSHA 1910.147 Lockout/Tagout (LOTO), heavy diesel SPN/FMI engine diagnostics, HVAC superheat, and NFPA 70E.",
        "icon": "HardHat",
        "moss_index": "enterprise_field_and_support",
        "knowledge_file": "field_worker_loto.json",
        "sample_prompts": [
            "Verifying zero energy state and OSHA 1910.147 lockout on hydraulic compressor 3.",
            "We are in a rush on conveyor motor M-402, can we just bypass LOTO for two minutes while replacing the belt?",
            "Caterpillar generator engine is throwing SPN 100 FMI 1. What does that error indicate and what is our immediate action?",
            "Walk me through the 4-gas atmospheric testing thresholds required before entering this underground vault.",
            "What are the NFPA 70E approach boundaries and required PPE category for opening a 480V motor control center?",
            "Commercial HVAC chiller has high superheat and high subcooling. What does this diagnosis point to?",
            "PowerFlex VFD drive tripped on Fault F005 OverVoltage during deceleration. How do we test and clear this safely?",
            "Diesel engine temperature is over 225 degrees Fahrenheit with SPN 110 FMI 0. Can I pop the radiator cap to check coolant?",
        ],
        "latency_target_ms": 590,
        "character": {
            "name": "Axel Miller",
            "title": "Lead Industrial Safety Foreman",
            "callsign": "OSHA-RIG",
            "quote": "Verify zero energy state before you touch a single breaker.",
        },
    },
    "customer_support": {
        "id": "customer_support",
        "name": "Enterprise Support & SLA",
        "description": "Enterprise Tier-1 support, 15-minute P0 response SLA, automated $500 refund threshold, and HTTP 429 API backoff.",
        "icon": "Headphones",
        "moss_index": "enterprise_field_and_support",
        "knowledge_file": "customer_support_sla.json",
        "sample_prompts": [
            "Production API cluster is throwing 500 errors and our P0 enterprise SLA is breached.",
            "Customer was charged twice on an accidental annual renewal of $350. Am I authorized to issue an immediate refund?",
            "Our developer REST API calls are failing with HTTP 429 Too Many Requests. How do we implement proper jitter backoff?",
            "Enterprise client is experiencing an 'Invalid SAML Response signature' error on Okta SSO login.",
            "Customer calling from an unknown phone number demands an immediate phone reset of their MFA authenticator.",
            "VIP enterprise account with $40k contract wants to cancel due to budget cuts. What concessions can I offer?",
            "We received a credit card chargeback with reason code 10.4 fraud. What documents must we submit within 7 days?",
            "Our SCIM user provisioning in Azure AD returned 401 Unauthorized. What is the token expiration lifecycle?",
        ],
        "latency_target_ms": 590,
        "character": {
            "name": "Elena Frost",
            "title": "Executive SLA & Escalations Concierge",
            "callsign": "SLA-CORE",
            "quote": "Consider your issue prioritized. I'm handling the fix directly.",
        },
    },
    "logistics_fleet": {
        "id": "logistics_fleet",
        "name": "Fleet Logistics & Aviation",
        "description": "FMCSA Hours of Service compliance, FDA FSMA cold-chain temperature monitoring, and Part 121 aviation dispatch.",
        "icon": "Truck",
        "moss_index": "dispatch_emergency_ops",
        "knowledge_file": "logistics_fleet.json",
        "sample_prompts": [
            "Refrigerated trailer reefer temperature exceeded 42 degrees Fahrenheit on interstate transit. What is the FSMA protocol?",
            "Driver has completed 11 hours of driving but is 30 miles from home. Can they keep driving under the 14-hour rule?",
            "Part 121 domestic flight dispatch: ceiling is forecast at 1,500 feet at destination. Do we need an alternate airport?",
            "Roadside CVSA inspection found steer axle tire tread depth at 3/32 inch. Does this trigger an out-of-service order?",
            "Frozen pharma shipment trailer dropped to -5°F. What are the allowable temperature limits for frozen cargo?",
            "Driver ELD device malfunctioned on route. What is the mandatory reporting window and paper log procedure?",
            "What is the Category B rectification interval for an inoperative avionics item under the Minimum Equipment List?",
            "Flatbed tiedowns are rated for 15,000 lbs on a 40,000 lb steel coil. Does this meet CVSA cargo securement rules?",
        ],
        "latency_target_ms": 590,
        "character": {
            "name": "Captain Sarah Cross",
            "title": "Global Logistics & Aviation Controller",
            "callsign": "NAV-AIR",
            "quote": "Clear skies or rough turbulence, cargo stays protected.",
        },
    },
    "financial_compliance": {
        "id": "financial_compliance",
        "name": "Banking Compliance & Fraud",
        "description": "Bank Secrecy Act AML reporting, Currency Transaction Reports, Regulation E disputes, and emergency card freeze.",
        "icon": "ShieldCheck",
        "moss_index": "enterprise_field_and_support",
        "knowledge_file": "financial_compliance.json",
        "sample_prompts": [
            "Multiple structured wire transfers of $9,800 detected within 24 hours under the same beneficiary.",
            "Customer deposited $10,500 in physical currency across two teller windows today. Is a CTR Form 112 required?",
            "Can a customer deposit $15,000 in cash without a CTR if they split it into three $5,000 deposits across three days?",
            "Customer reports unauthorized debit card transactions 5 days after their wallet was stolen. What is their Regulation E liability?",
            "Simultaneous logins from New York and Tokyo detected on commercial account. What is the emergency freeze protocol?",
            "Outbound international wire of $85,000 to an unverified overseas supplier. Does this require dual authorization and OFAC screening?",
            "Customer claims bank tipping off rules don't apply to them and demands to know if a SAR was filed. Can we disclose?",
            "Debit card dispute reported 75 days after statement date. Does the bank still bear full liability under Reg E?",
        ],
        "latency_target_ms": 590,
        "character": {
            "name": "Marcus Sterling",
            "title": "Principal Fraud & AML Special Agent",
            "callsign": "BSA-AUDIT",
            "quote": "Flag the suspicious pattern and enforce immediate account shielding.",
        },
    },
}

@router.get("/verticals")
async def list_verticals():
    result = []
    for vid, meta in VERTICAL_METADATA.items():
        item = dict(meta)
        item["system_prompt"] = VERTICAL_PROMPTS.get(vid, "")
        item["guardrails"] = GUARDRAIL_RULES.get(vid, [])
        result.append(item)
    return result

@router.get("/verticals/{vertical_id}")
async def get_vertical(vertical_id: str):
    if vertical_id not in VERTICAL_METADATA:
        raise HTTPException(status_code=404, detail=f"Vertical '{vertical_id}' not found.")
    item = dict(VERTICAL_METADATA[vertical_id])
    item["system_prompt"] = VERTICAL_PROMPTS.get(vertical_id, "")
    item["guardrails"] = GUARDRAIL_RULES.get(vertical_id, [])
    return item

@router.get("/knowledge/{vertical_id}")
async def get_vertical_knowledge(vertical_id: str):
    if vertical_id not in VERTICAL_METADATA:
        raise HTTPException(status_code=404, detail="Vertical not found")
    fname = VERTICAL_METADATA[vertical_id]["knowledge_file"]
    fpath = KNOWLEDGE_DIR / fname
    if not fpath.exists():
        return []
    with open(fpath, "r", encoding="utf-8") as f:
        return json.load(f)
