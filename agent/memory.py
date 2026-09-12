"""Multi-Turn Conversation History & Contextual Query Rewriter.

Resolves pronouns, elliptical questions, and follow-up turns into explicit search
queries for Moss sub-10ms context retrieval.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

@dataclass
class ConversationTurn:
    turn_id: int
    user_text: str
    agent_text: str
    retrieved_doc_ids: List[str] = field(default_factory=list)
    key_entities: List[str] = field(default_factory=list)

class SessionMemoryManager:
    """In-memory rolling multi-turn session cache per room/call."""
    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self._sessions: Dict[str, List[ConversationTurn]] = {}

    def get_history(self, call_id: str) -> List[ConversationTurn]:
        return self._sessions.get(call_id, [])

    def record_turn(
        self,
        call_id: str,
        turn_id: int,
        user_text: str,
        agent_text: str,
        retrieved_doc_ids: Optional[List[str]] = None
    ) -> None:
        if call_id not in self._sessions:
            self._sessions[call_id] = []
        
        entities = self._extract_entities(user_text)
        turn = ConversationTurn(
            turn_id=turn_id,
            user_text=user_text,
            agent_text=agent_text,
            retrieved_doc_ids=retrieved_doc_ids or [],
            key_entities=entities
        )
        self._sessions[call_id].append(turn)
        if len(self._sessions[call_id]) > self.max_history:
            self._sessions[call_id].pop(0)

    def _extract_entities(self, text: str) -> List[str]:
        # Extract potential nouns / entity terms (e.g. "Unit 4", "Code 3", "LOTO", "transformer", "chlorine")
        tokens = re.findall(r"\b[A-Za-z0-9\-\_]{3,}\b", text)
        stopwords = {"what", "when", "where", "which", "about", "there", "their", "please", "could", "would", "should"}
        return [t for t in tokens if t.lower() not in stopwords]

    def expand_query(self, call_id: str, current_query: str) -> str:
        """Expands elliptical follow-ups like 'What about the perimeter?' using previous turn context."""
        history = self.get_history(call_id)
        if not history:
            return current_query
        
        clean = current_query.strip().lower()
        pronoun_markers = [
            "what about", "how about", "and its", "and their", "the distance",
            "the perimeter", "the protocol", "the dosage", "what next",
            "what then", "and then", "why", "who", "it", "them", "those"
        ]
        
        is_followup = (
            len(clean.split()) <= 6 and 
            any(m in clean for m in pronoun_markers)
        )
        
        if is_followup:
            last_turn = history[-1]
            # Gather salient anchor keywords from previous turn
            anchors = last_turn.key_entities[:3]
            if anchors:
                expanded = f"{current_query} ({' '.join(anchors)})"
                return expanded

        return current_query

# Global singleton memory manager
memory_manager = SessionMemoryManager()
