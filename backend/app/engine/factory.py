from typing import Optional
from app.core.config import settings
from app.engine.base import BaseDecisionEngine
from app.engine.rule_engine import RuleBasedDecisionEngine
from app.engine.llm_engine import LLMDecisionEngine

def get_decision_engine(engine_type: Optional[str] = None) -> BaseDecisionEngine:
    """Factory function resolving decision engine instance based on configuration or explicit type."""
    selected_type = (engine_type or settings.DECISION_ENGINE_TYPE).lower()

    if selected_type == "llm":
        return LLMDecisionEngine()
    
    return RuleBasedDecisionEngine()
