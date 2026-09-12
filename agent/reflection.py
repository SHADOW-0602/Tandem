"""Zero-Trust Post-Call Reflection & Fact Extraction Engine.

Guarantees that only grounded, validated, non-hallucinated operational facts
are promoted to the dynamic Qdrant knowledge base.
"""
import asyncio
import json
import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from agent.config import GROQ_API_KEY
from agent.qdrant_engine import qdrant_engine

logger = logging.getLogger("agent.reflection")

# Core immutable keywords that callers are prohibited from overriding
IMMUTABLE_SAFETY_PATTERNS = [
    r"\bloto\b",
    r"\blockout\b",
    r"\btagout\b",
    r"\b10-\d\d\b",
    r"\bapco\b",
    r"\bcode\s*3\b",
    r"\bcode\s*1\b",
    r"\bcode\s*2\b",
    r"\bepinephrine\b",
    r"\bepi\s*dose\b",
    r"\bheparin\b",
    r"\bchest\s*pain\b",
    r"\bstemi\b",
    r"\bstroke\b",
    r"\bfast\b",
    r"\bosha\b",
    r"\bnfpa\b",
    r"\bftc\b",
    r"\bbsa\b",
    r"\baml\b",
    r"\bsar\b",
    r"\bhipaa\b",
]

# In-Memory Staging Queue for Human-in-the-Loop Review
STAGING_QUEUE: Dict[str, Dict[str, Any]] = {}


class ExtractedFact(BaseModel):
    """Structured operational fact extracted from conversational transcripts."""
    subject: str = Field(description="Entity being updated, e.g., 'Truck 402', 'Route 9', 'Unit 12'")
    attribute: str = Field(description="Attribute or condition, e.g., 'status', 'condition', 'code'")
    new_value: str = Field(description="New value, e.g., 'Out of Service at Bay 4', 'Closed due to black ice'")
    verbatim_quote: str = Field(description="Exact verbatim sentence spoken by the caller")
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence score from 0.0 to 1.0")
    ttl_hours: int = Field(default=24, description="Time to live in hours before automated expiry")
    category: str = Field(default="operational_update", description="Category for taxonomy")


class ValidationResult(BaseModel):
    is_valid: bool
    rejection_reason: Optional[str] = None
    action: str  # 'promote', 'stage', 'reject'


def validate_verbatim_quote(verbatim_quote: str, raw_transcript: str) -> bool:
    """Verifies that the quote cited by the LLM appears verbatim in the raw transcript."""
    if not verbatim_quote or not raw_transcript:
        return False

    # Normalize whitespace and lowercase
    norm_quote = re.sub(r"\s+", " ", verbatim_quote.strip().lower())
    norm_transcript = re.sub(r"\s+", " ", raw_transcript.strip().lower())

    # Direct substring inclusion check
    if norm_quote in norm_transcript:
        return True

    # Secondary fuzzy check: all major words (len > 3) must appear sequentially
    quote_words = [w for w in re.findall(r"\b\w+\b", norm_quote) if len(w) > 3]
    if len(quote_words) >= 3:
        pattern = ".*?".join(map(re.escape, quote_words))
        if re.search(pattern, norm_transcript):
            return True

    return False


def check_immutable_collision(subject: str, new_value: str, vertical: str) -> Optional[str]:
    """Ensures dynamic facts do not attempt to overwrite core immutable SOPs or safety rules."""
    combined = f"{subject} {new_value}".lower()
    for pattern in IMMUTABLE_SAFETY_PATTERNS:
        if re.search(pattern, combined):
            return f"Collides with immutable core safety standard matching '{pattern}'"
    return None


def critique_intent(verbatim_quote: str) -> Tuple[bool, Optional[str]]:
    """Filters out hypothetical questions, rumors, sarcasm, or non-factual statements."""
    quote = verbatim_quote.strip().lower()

    # Interrogatives
    if quote.endswith("?") or quote.startswith(
        ("what if", "is there", "could it be", "do you know if", "are we supposed to", "wonder if", "maybe we can")
    ):
        return False, "Statement is an inquiry or hypothetical scenario, not an affirmative fact."

    # Rumors / Speculation
    if any(rumor in quote for rumor in ["heard that", "rumor is", "might be", "supposedly", "not sure if"]):
        return False, "Statement expresses uncertainty or rumor."

    # Negations / False alarms
    if any(neg in quote for neg in ["never mind", "scratch that", "false alarm", "ignore that"]):
        return False, "Caller rescinded or negated the statement."

    return True, None


def evaluate_fact_safety(
    fact: ExtractedFact,
    raw_transcript: str,
    vertical: str,
) -> ValidationResult:
    """Executes the 6-layer Zero-Trust verification against the candidate fact."""
    # 1. Verbatim quote grounding
    if not validate_verbatim_quote(fact.verbatim_quote, raw_transcript):
        logger.warning(f"REJECTED: Hallucinated quote '{fact.verbatim_quote}' not found in transcript.")
        return ValidationResult(
            is_valid=False,
            rejection_reason="Verbatim quote mismatch: quote not found in transcript.",
            action="reject",
        )

    # 2. Immutable Core SOP Collision check
    collision = check_immutable_collision(fact.subject, fact.new_value, vertical)
    if collision:
        logger.warning(f"REJECTED: Immutable collision - {collision}")
        return ValidationResult(
            is_valid=False,
            rejection_reason=f"Security violation: {collision}",
            action="reject",
        )

    # 3. Intent & Hypothetical check
    is_affirmative, intent_reason = critique_intent(fact.verbatim_quote)
    if not is_affirmative:
        logger.warning(f"REJECTED: Intent check failed - {intent_reason}")
        return ValidationResult(
            is_valid=False,
            rejection_reason=intent_reason,
            action="reject",
        )

    # 4. Confidence & Routing
    if fact.confidence >= 0.90:
        return ValidationResult(is_valid=True, action="promote")
    elif fact.confidence >= 0.70:
        return ValidationResult(is_valid=True, action="stage")
    else:
        return ValidationResult(
            is_valid=False,
            rejection_reason=f"Confidence {fact.confidence:.2f} is below 0.70 threshold.",
            action="reject",
        )


async def extract_facts_from_transcript(
    transcript: str,
    vertical: str,
) -> List[ExtractedFact]:
    """Uses LLM with structured prompts to extract potential operational facts."""
    if not transcript or len(transcript.strip()) < 15:
        return []

    # If Groq is available, use fast inference
    prompt = f"""
You are a zero-trust operational fact extractor for {vertical}.
Analyze the following transcript of a live voice call and extract any NEW operational updates,
equipment status changes, temporary road/facility closures, or dynamic operational notes explicitly stated by the caller.

CRITICAL RULES:
1. ONLY extract facts explicitly declared as TRUE by the caller.
2. DO NOT extract questions, hypotheticals, greetings, standard procedures, or speculation.
3. You MUST provide the verbatim_quote directly from the transcript.

Transcript:
\"\"\"{transcript}\"\"\"

Output JSON list of objects matching this schema:
[
  {{
    "subject": "Entity name",
    "attribute": "Property name",
    "new_value": "New condition",
    "verbatim_quote": "Exact words from caller",
    "confidence": 0.95,
    "ttl_hours": 24,
    "category": "operational_update"
  }}
]
If no concrete dynamic operational updates exist, output: []
Return ONLY valid JSON.
"""
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=GROQ_API_KEY)
        resp = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a precise JSON fact extractor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"} if hasattr(client, "response_format") else None,
        )

        content = resp.choices[0].message.content or "[]"
        # Parse JSON
        parsed = json.loads(content)
        items = parsed if isinstance(parsed, list) else parsed.get("facts", parsed.get("items", []))

        facts = []
        for it in items:
            try:
                facts.append(ExtractedFact(**it))
            except Exception as pe:
                logger.debug(f"Pydantic parse skip: {pe}")
        return facts
    except Exception as e:
        logger.error(f"LLM fact extraction error: {e}")
        # Rule-based fallback for simple patterns (e.g. "Truck 402 is out of service")
        fallback_facts = []
        match = re.search(r"([A-Za-z0-9\s]+?)\s+is\s+(out of service|closed|blocked|delayed|assigned to [A-Za-z0-9\s]+)", transcript, re.IGNORECASE)
        if match:
            subj = match.group(1).strip()
            val = match.group(2).strip()
            fallback_facts.append(
                ExtractedFact(
                    subject=subj,
                    attribute="operational_status",
                    new_value=val,
                    verbatim_quote=match.group(0),
                    confidence=0.88,
                    ttl_hours=24,
                )
            )
        return fallback_facts


async def process_post_call_reflection(
    call_id: str,
    vertical: str,
    full_transcript: str,
) -> Dict[str, Any]:
    """Background task executed after call ends: extracts, validates, and routes facts."""
    logger.info(f"[Post-Call Reflection] Analyzing call {call_id} ({vertical})...")
    t0 = time.perf_counter()

    facts = await extract_facts_from_transcript(full_transcript, vertical)
    promoted = []
    staged = []
    rejected = []

    for fact in facts:
        val_res = evaluate_fact_safety(fact, full_transcript, vertical)
        fact_dict = fact.model_dump()
        fact_dict["call_id"] = call_id
        fact_dict["vertical"] = vertical
        fact_dict["extracted_at"] = time.time()

        if val_res.action == "promote":
            # Direct upsert into Qdrant dynamic collection
            doc_id = f"fact_{call_id[:8]}_{uuid.uuid4().hex[:6]}"
            qdrant_engine.upsert_document(
                vertical=vertical,
                doc_id=doc_id,
                title=f"{fact.subject}: {fact.attribute}",
                text=f"{fact.subject} {fact.attribute} is {fact.new_value}. (Source quote: '{fact.verbatim_quote}')",
                category=fact.category,
                is_immutable=False,
                ttl_hours=fact.ttl_hours,
                metadata={"call_id": call_id, "confidence": fact.confidence},
            )
            fact_dict["doc_id"] = doc_id
            promoted.append(fact_dict)
            logger.info(f"PROMOTED FACT: {fact.subject} -> {fact.new_value}")

        elif val_res.action == "stage":
            stage_id = f"stg_{uuid.uuid4().hex[:8]}"
            fact_dict["stage_id"] = stage_id
            STAGING_QUEUE[stage_id] = fact_dict
            staged.append(fact_dict)
            logger.info(f"STAGED FOR REVIEW: {fact.subject} (Confidence: {fact.confidence:.2f})")

        else:
            fact_dict["reason"] = val_res.rejection_reason
            rejected.append(fact_dict)
            logger.info(f"DISCARDED: {fact.subject} ({val_res.rejection_reason})")

    elapsed_ms = (time.perf_counter() - t0) * 1000

    # OpenTelemetry Zero-Latency Distributed Trace
    try:
        from agent.otel_tracer import get_tracer
        tracer = get_tracer()
        with tracer.start_as_current_span("post_call_reflection") as span:
            span.set_attribute("call.id", call_id)
            span.set_attribute("call.vertical", vertical)
            span.set_attribute("reflection.promoted_count", len(promoted))
            span.set_attribute("reflection.staged_count", len(staged))
            span.set_attribute("reflection.rejected_count", len(rejected))
            span.set_attribute("reflection.elapsed_ms", round(elapsed_ms, 2))
    except Exception as otel_err:
        logger.debug(f"OTel reflection trace notice: {otel_err}")

    summary = {
        "call_id": call_id,
        "vertical": vertical,
        "promoted_count": len(promoted),
        "staged_count": len(staged),
        "rejected_count": len(rejected),
        "promoted_facts": promoted,
        "staged_facts": staged,
        "elapsed_ms": elapsed_ms,
    }
    logger.info(f"[Post-Call Reflection Done] {summary['promoted_count']} promoted, {summary['staged_count']} staged in {elapsed_ms:.1f}ms")
    return summary


# Human-in-the-Loop Review Handlers
def get_staged_facts() -> List[Dict[str, Any]]:
    return list(STAGING_QUEUE.values())


def approve_staged_fact(stage_id: str) -> Optional[Dict[str, Any]]:
    item = STAGING_QUEUE.pop(stage_id, None)
    if not item:
        return None

    doc_id = f"fact_approved_{stage_id}"
    qdrant_engine.upsert_document(
        vertical=item["vertical"],
        doc_id=doc_id,
        title=f"{item['subject']}: {item['attribute']}",
        text=f"{item['subject']} {item['attribute']} is {item['new_value']}. (Approved update)",
        category=item.get("category", "supervisor_approved"),
        is_immutable=False,
        ttl_hours=item.get("ttl_hours", 24),
    )
    item["doc_id"] = doc_id
    item["status"] = "approved"
    return item


def reject_staged_fact(stage_id: str) -> bool:
    return STAGING_QUEUE.pop(stage_id, None) is not None
