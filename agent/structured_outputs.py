"""Post-call Structured Output Extraction Engine — powered by Google Gemini.

Runs after every call ends. Reads the full conversation transcript, evaluates
conditions (minMessages, minCallDuration, endedReason), then calls Gemini with
JSON mode to extract schema-defined fields from the conversation.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("agent.structured_outputs")

# ---------------------------------------------------------------------------
# Default JSON Schemas — one per vertical
# Edit these to change what gets extracted for every call in that domain.
# ---------------------------------------------------------------------------
VERTICAL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "dispatch": {
        "name": "Dispatch Incident Summary",
        "description": "Extract tactical incident information from a CAD dispatch conversation.",
        "schema": {
            "type": "object",
            "properties": {
                "incidentType": {
                    "type": "string",
                    "description": "Nature of the incident (e.g. 'Traffic Stop', 'Domestic Disturbance', 'HAZMAT', 'Active Shooter')"
                },
                "unitId": {
                    "type": "string",
                    "description": "Primary responding unit designation (e.g. 'Unit 12', 'Alpha-7')"
                },
                "location": {
                    "type": "string",
                    "description": "Incident location as mentioned in conversation"
                },
                "priorityCode": {
                    "type": "string",
                    "enum": ["Code 1", "Code 2", "Code 3", "Unknown"],
                    "description": "Dispatch priority code"
                },
                "tenCodesUsed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "APCO 10-codes mentioned during the conversation (e.g. ['10-4', '10-23'])"
                },
                "hazmatInvolved": {
                    "type": "boolean",
                    "description": "Whether a HAZMAT situation was discussed"
                },
                "escalatedToCommandSupervisor": {
                    "type": "boolean",
                    "description": "Whether a Code Red or Watch Commander escalation was triggered"
                }
            },
            "required": ["incidentType", "hazmatInvolved", "escalatedToCommandSupervisor"]
        }
    },
    "healthcare": {
        "name": "Clinical Triage Summary",
        "description": "Extract patient and clinical information from a triage conversation.",
        "schema": {
            "type": "object",
            "properties": {
                "chiefComplaint": {
                    "type": "string",
                    "description": "Patient's primary complaint or presenting symptom"
                },
                "esiLevel": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 5,
                    "description": "Emergency Severity Index level assigned (1=most critical, 5=least urgent)"
                },
                "vitalsCollected": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Vital signs discussed (e.g. ['blood pressure', 'oxygen saturation', 'heart rate'])"
                },
                "protocolsReferenced": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Clinical protocols mentioned (e.g. ['STEMI', 'FAST stroke', 'ACS', 'anaphylaxis'])"
                },
                "emergencyEscalationTriggered": {
                    "type": "boolean",
                    "description": "Whether a 911 emergency escalation was issued"
                },
                "clinicalDisclaimerIssued": {
                    "type": "boolean",
                    "description": "Whether the AI disclaimer was stated (cannot diagnose/prescribe)"
                },
                "patientAgeEstimate": {
                    "type": "string",
                    "description": "Age or age range of patient if mentioned"
                }
            },
            "required": ["emergencyEscalationTriggered", "clinicalDisclaimerIssued"]
        }
    },
    "field_worker": {
        "name": "Field Maintenance Report",
        "description": "Extract equipment, safety, and procedure details from a field maintenance conversation.",
        "schema": {
            "type": "object",
            "properties": {
                "equipmentId": {
                    "type": "string",
                    "description": "Equipment or machine identifier mentioned"
                },
                "faultCodes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "SPN/FMI fault codes or error codes discussed (e.g. ['SPN 3864 FMI 5'])"
                },
                "procedurePerformed": {
                    "type": "string",
                    "description": "Primary maintenance or safety procedure discussed"
                },
                "lotoCompleted": {
                    "type": "boolean",
                    "description": "Whether a full lockout/tagout (LOTO) procedure was completed"
                },
                "ppeCategoryRequired": {
                    "type": "string",
                    "description": "NFPA 70E PPE category level required (e.g. 'Category 2')"
                },
                "safetyViolationDetected": {
                    "type": "boolean",
                    "description": "Whether a safety violation or OSHA non-compliance was flagged"
                },
                "evacuationIssued": {
                    "type": "boolean",
                    "description": "Whether an emergency evacuation was ordered"
                }
            },
            "required": ["lotoCompleted", "safetyViolationDetected", "evacuationIssued"]
        }
    },
    "customer_support": {
        "name": "Support Interaction Summary",
        "description": "Extract issue details, resolution, and escalation from a customer support conversation.",
        "schema": {
            "type": "object",
            "properties": {
                "issueType": {
                    "type": "string",
                    "enum": ["billing", "api_error", "sla_question", "account", "sso_auth", "legal", "other"],
                    "description": "Primary category of the support request"
                },
                "accountId": {
                    "type": "string",
                    "description": "Customer account ID or email mentioned"
                },
                "resolutionProvided": {
                    "type": "boolean",
                    "description": "Whether a resolution was provided during the call"
                },
                "refundAmount": {
                    "type": "number",
                    "description": "Dollar amount of refund discussed or approved (0 if none)"
                },
                "escalationRequired": {
                    "type": "boolean",
                    "description": "Whether escalation to Tier-2 or Legal was initiated"
                },
                "httpErrorCode": {
                    "type": "string",
                    "description": "HTTP error code discussed if applicable (e.g. '429', '500')"
                },
                "satisfactionSignal": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral", "unclear"],
                    "description": "Inferred caller sentiment at end of conversation"
                }
            },
            "required": ["issueType", "resolutionProvided", "escalationRequired", "satisfactionSignal"]
        }
    },
    "logistics_fleet": {
        "name": "Fleet Compliance Report",
        "description": "Extract HOS, cargo, and safety information from a fleet logistics conversation.",
        "schema": {
            "type": "object",
            "properties": {
                "driverId": {
                    "type": "string",
                    "description": "Driver or unit identifier mentioned"
                },
                "hoursReported": {
                    "type": "object",
                    "properties": {
                        "drivingHours": {"type": "number"},
                        "onDutyHours": {"type": "number"}
                    },
                    "description": "Hours reported by the driver"
                },
                "hosViolationDetected": {
                    "type": "boolean",
                    "description": "Whether an FMCSA Hours of Service violation was flagged"
                },
                "cargoTemperatureF": {
                    "type": "number",
                    "description": "Reefer/cargo temperature reported in Fahrenheit"
                },
                "reeferBreachDetected": {
                    "type": "boolean",
                    "description": "Whether a cold-chain temperature exceedance was detected"
                },
                "cvsaIssue": {
                    "type": "string",
                    "description": "CVSA out-of-service issue mentioned if any"
                },
                "roadEmergencyIssued": {
                    "type": "boolean",
                    "description": "Whether an emergency pullover instruction was given"
                }
            },
            "required": ["hosViolationDetected", "reeferBreachDetected", "roadEmergencyIssued"]
        }
    },
    "financial_compliance": {
        "name": "Compliance Interaction Record",
        "description": "Extract compliance, transaction, and fraud details from a banking compliance conversation.",
        "schema": {
            "type": "object",
            "properties": {
                "transactionType": {
                    "type": "string",
                    "enum": ["cash_deposit", "cash_withdrawal", "wire_transfer", "dispute", "other"],
                    "description": "Type of transaction discussed"
                },
                "amountMentioned": {
                    "type": "number",
                    "description": "Dollar amount mentioned in context of the transaction"
                },
                "ctrRequired": {
                    "type": "boolean",
                    "description": "Whether a Currency Transaction Report (CTR) is required"
                },
                "sarConcernDetected": {
                    "type": "boolean",
                    "description": "Whether suspicious activity indicators were raised (do NOT confirm SAR filing)"
                },
                "structuringAttemptDetected": {
                    "type": "boolean",
                    "description": "Whether the caller appeared to ask about structuring transactions"
                },
                "regulationEClaim": {
                    "type": "boolean",
                    "description": "Whether a Regulation E unauthorized transaction dispute was discussed"
                },
                "accountFreezeInitiated": {
                    "type": "boolean",
                    "description": "Whether an emergency account freeze was initiated"
                },
                "liabilityTierApplied": {
                    "type": "string",
                    "enum": ["2-day", "60-day", "unlimited", "none"],
                    "description": "Regulation E liability tier that was applied"
                }
            },
            "required": ["ctrRequired", "sarConcernDetected", "structuringAttemptDetected",
                         "regulationEClaim", "accountFreezeInitiated"]
        }
    }
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class ExtractionCondition:
    type: str                          # "minMessages" | "minCallDuration" | "endedReason"
    count: Optional[int] = None        # for minMessages
    seconds: Optional[int] = None      # for minCallDuration
    operator: Optional[str] = None     # "oneOf" | "notOneOf"
    values: Optional[List[str]] = None # for endedReason


@dataclass
class ExtractionResult:
    schema_id: str
    name: str
    vertical: str
    call_id: str
    result: Optional[Dict[str, Any]]    # None if extraction failed or was skipped
    skipped: bool = False
    skip_reason: Optional[str] = None
    extraction_model: str = "gemini-2.0-flash"
    duration_ms: float = 0.0
    extracted_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Condition evaluator
# ---------------------------------------------------------------------------
class ConditionEvaluator:
    """Evaluates whether a call meets all conditions for extraction to run."""

    @staticmethod
    def evaluate(
        conditions: List[Dict[str, Any]],
        message_count: int,
        call_duration_seconds: float,
        ended_reason: str = "unknown"
    ) -> tuple[bool, Optional[str]]:
        """Returns (should_run, skip_reason). skip_reason is None when should_run=True."""
        for cond in conditions:
            ctype = cond.get("type")
            if ctype == "minMessages":
                required = cond.get("count", 0)
                if message_count < required:
                    return False, f"minMessages not met: {message_count} < {required}"
            elif ctype == "minCallDuration":
                required = cond.get("seconds", 0)
                if call_duration_seconds < required:
                    return False, f"minCallDuration not met: {call_duration_seconds:.1f}s < {required}s"
            elif ctype == "endedReason":
                operator = cond.get("operator", "oneOf")
                values = cond.get("values", [])
                if operator == "oneOf" and ended_reason not in values:
                    return False, f"endedReason '{ended_reason}' not in {values}"
                elif operator == "notOneOf" and ended_reason in values:
                    return False, f"endedReason '{ended_reason}' is in excluded {values}"
        return True, None


# ---------------------------------------------------------------------------
# Transcript builder
# ---------------------------------------------------------------------------
def build_transcript(history) -> str:
    """Converts memory_manager conversation turns into a readable transcript string."""
    if not history:
        return ""
    lines = []
    for turn in history:
        if turn.user_text:
            lines.append(f"User: {turn.user_text}")
        if turn.agent_text and turn.agent_text != "Response synthesized with SOP":
            lines.append(f"Agent: {turn.agent_text}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gemini extraction engine
# ---------------------------------------------------------------------------
class StructuredOutputExtractor:
    """Extracts structured data from a call transcript using Google Gemini."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise RuntimeError(
                    "google-genai is not installed. Run: pip install google-genai>=1.0.0"
                )
        return self._client

    async def extract(
        self,
        *,
        call_id: str,
        schema_id: str,
        schema_def: Dict[str, Any],
        transcript: str,
        conditions: Optional[List[Dict[str, Any]]] = None,
        message_count: int = 0,
        call_duration_seconds: float = 0.0,
        ended_reason: str = "unknown",
        custom_model: Optional[Dict[str, Any]] = None,
    ) -> ExtractionResult:
        vertical = schema_def.get("vertical", "")
        name = schema_def.get("name", schema_id)
        schema = schema_def.get("schema", {})

        # 1. Evaluate conditions
        if conditions:
            should_run, skip_reason = ConditionEvaluator.evaluate(
                conditions, message_count, call_duration_seconds, ended_reason
            )
            if not should_run:
                logger.info(f"[{call_id}] Extraction '{name}' skipped: {skip_reason}")
                return ExtractionResult(
                    schema_id=schema_id, name=name, vertical=vertical,
                    call_id=call_id, result=None, skipped=True, skip_reason=skip_reason,
                    extraction_model=self.model_name,
                )

        if not transcript.strip():
            return ExtractionResult(
                schema_id=schema_id, name=name, vertical=vertical,
                call_id=call_id, result=None, skipped=True,
                skip_reason="Empty transcript — no turns recorded",
                extraction_model=self.model_name,
            )

        # 2. Build extraction prompt
        system_instruction = (
            "You are a precise data extraction assistant. "
            "Extract information from the conversation transcript strictly according to the JSON schema provided. "
            "Return ONLY valid JSON matching the schema. "
            "If a field cannot be determined from the transcript, omit it (or use null for required fields). "
            "Do not add fields that are not in the schema. "
            "Do not include any explanation or commentary — JSON only."
        )

        model_name = self.model_name
        temperature = 0.1

        if custom_model:
            model_name = custom_model.get("model", model_name)
            temperature = custom_model.get("temperature", temperature)

        extraction_prompt = (
            f"Schema name: {name}\n"
            f"Schema definition:\n{json.dumps(schema, indent=2)}\n\n"
            f"Conversation transcript:\n{transcript}\n\n"
            "Extract the fields from the transcript according to the schema above."
        )

        # 3. Call Gemini with JSON response type
        t0 = time.perf_counter()
        try:
            from google import genai
            from google.genai import types

            client = self._get_client()

            response = client.models.generate_content(
                model=model_name,
                contents=extraction_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=temperature,
                    max_output_tokens=1024,
                ),
            )

            duration_ms = (time.perf_counter() - t0) * 1000
            raw_text = response.text.strip()

            # Parse JSON response
            try:
                result = json.loads(raw_text)
            except json.JSONDecodeError as je:
                logger.warning(f"[{call_id}] Gemini returned invalid JSON for '{name}': {je}")
                result = None

            logger.info(
                f"[{call_id}] Extracted '{name}' in {duration_ms:.0f}ms "
                f"— fields: {list(result.keys()) if result else 'none'}"
            )
            return ExtractionResult(
                schema_id=schema_id, name=name, vertical=vertical,
                call_id=call_id, result=result, skipped=False,
                extraction_model=model_name, duration_ms=round(duration_ms, 1),
            )

        except Exception as e:
            duration_ms = (time.perf_counter() - t0) * 1000
            logger.error(f"[{call_id}] Extraction failed for '{name}': {e}")
            return ExtractionResult(
                schema_id=schema_id, name=name, vertical=vertical,
                call_id=call_id, result=None, skipped=False,
                skip_reason=f"Extraction error: {e}",
                extraction_model=model_name, duration_ms=round(duration_ms, 1),
            )


# ---------------------------------------------------------------------------
# Global extractor singleton (lazy-initialized)
# ---------------------------------------------------------------------------
_extractor: Optional[StructuredOutputExtractor] = None

def get_extractor() -> StructuredOutputExtractor:
    global _extractor
    if _extractor is None:
        from agent.config import GEMINI_API_KEY, GEMINI_EXTRACTION_MODEL
        _extractor = StructuredOutputExtractor(
            api_key=GEMINI_API_KEY,
            model_name=GEMINI_EXTRACTION_MODEL,
        )
    return _extractor


# ---------------------------------------------------------------------------
# High-level convenience function
# ---------------------------------------------------------------------------
async def run_extraction_for_call(
    call_id: str,
    vertical: str,
    message_count: int,
    call_duration_seconds: float,
    ended_reason: str = "agent-ended-call",
    custom_schemas: Optional[List[Dict[str, Any]]] = None,
) -> List[ExtractionResult]:
    """Runs all applicable structured output extractions for a completed call.

    Uses the default VERTICAL_SCHEMAS for the given vertical plus any
    custom_schemas passed in (from the server schema registry).

    Returns a list of ExtractionResult objects (one per schema).
    """
    from agent.memory import memory_manager

    history = memory_manager.get_history(call_id)
    transcript = build_transcript(history)
    extractor = get_extractor()

    # Collect schemas to run: default vertical schema + custom schemas
    schemas_to_run: List[Dict[str, Any]] = []

    default = VERTICAL_SCHEMAS.get(vertical)
    if default:
        schemas_to_run.append({
            "schema_id": f"default_{vertical}",
            "vertical": vertical,
            **default,
            "conditions": [],
        })

    if custom_schemas:
        for cs in custom_schemas:
            schemas_to_run.append(cs)

    results: List[ExtractionResult] = []
    for schema_def in schemas_to_run:
        result = await extractor.extract(
            call_id=call_id,
            schema_id=schema_def.get("schema_id", schema_def.get("name", "custom")),
            schema_def={**schema_def, "vertical": vertical},
            transcript=transcript,
            conditions=schema_def.get("conditions", []),
            message_count=message_count,
            call_duration_seconds=call_duration_seconds,
            ended_reason=ended_reason,
        )
        results.append(result)

    return results
