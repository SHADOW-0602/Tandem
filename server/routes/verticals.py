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
            "Unit 4 reporting a 10-50 on Route 9, request backup status",
            "What is the initial isolation distance for a chlorine gas leak?",
            "Officer down on scene, Signal 13, need immediate assistance",
        ],
        "latency_target_ms": 590,
    },
    "healthcare": {
        "id": "healthcare",
        "name": "Clinical & Emergency Triage",
        "description": "Hospital triage & clinical support covering ESI Levels 1-5, ACS cardiac protocols, Cincinnati Stroke FAST, and HIPAA.",
        "icon": "Stethoscope",
        "moss_index": "clinical_healthcare_triage",
        "knowledge_file": "healthcare_triage.json",
        "sample_prompts": [
            "Patient has crushing substernal chest pain and shortness of breath",
            "What are the FAST stroke screening steps and therapeutic window?",
            "What is the adult intramuscular dose for epinephrine in anaphylaxis?",
        ],
        "latency_target_ms": 590,
    },
    "field_worker": {
        "id": "field_worker",
        "name": "Field Ops & Industrial Safety",
        "description": "OSHA 1910.147 Lockout/Tagout (LOTO), heavy diesel SPN/FMI engine diagnostics, HVAC superheat, and NFPA 70E.",
        "icon": "HardHat",
        "moss_index": "enterprise_field_and_support",
        "knowledge_file": "field_worker_loto.json",
        "sample_prompts": [
            "Walk me through the 6 steps of OSHA Lockout Tagout zero energy verification",
            "Caterpillar engine is throwing SPN 100 FMI 1, what does that mean?",
            "What are the 4-gas atmospheric limits for confined space entry?",
        ],
        "latency_target_ms": 590,
    },
    "customer_support": {
        "id": "customer_support",
        "name": "Enterprise Support & SLA",
        "description": "Enterprise Tier-1 support, 15-minute P0 response SLA, automated $500 refund threshold, and HTTP 429 API backoff.",
        "icon": "Headphones",
        "moss_index": "enterprise_field_and_support",
        "knowledge_file": "customer_support_sla.json",
        "sample_prompts": [
            "What is our response SLA for a P0 critical system outage?",
            "Can I issue an immediate $350 refund for an accidental renewal?",
            "Customer is getting HTTP 429 errors on the REST API, how to troubleshoot?",
        ],
        "latency_target_ms": 590,
    },
    "logistics_fleet": {
        "id": "logistics_fleet",
        "name": "Fleet Logistics & Aviation",
        "description": "FMCSA Hours of Service compliance, FDA FSMA cold-chain temperature monitoring, and Part 121 aviation dispatch.",
        "icon": "Truck",
        "moss_index": "dispatch_emergency_ops",
        "knowledge_file": "logistics_fleet.json",
        "sample_prompts": [
            "What is the FMCSA 11-hour driving rule and 14-hour on-duty window?",
            "Reefer temperature just exceeded 42 degrees, what is the protocol?",
            "What is the alternate airport fuel reserve requirement under Part 121?",
        ],
        "latency_target_ms": 590,
    },
    "financial_compliance": {
        "id": "financial_compliance",
        "name": "Banking Compliance & Fraud",
        "description": "Bank Secrecy Act AML reporting, Currency Transaction Reports, Regulation E disputes, and emergency card freeze.",
        "icon": "ShieldCheck",
        "moss_index": "enterprise_field_and_support",
        "knowledge_file": "financial_compliance.json",
        "sample_prompts": [
            "When is a Currency Transaction Report mandatory under BSA?",
            "What are the consumer liability tiers for unauthorized transfers under Reg E?",
            "Customer reports unauthorized debit transactions, what is the emergency freeze protocol?",
        ],
        "latency_target_ms": 590,
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
