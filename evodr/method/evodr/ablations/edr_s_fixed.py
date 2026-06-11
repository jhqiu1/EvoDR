from ..evodr import EVODR
from .suggestion_bank import SUGGESTIONS


class EDR_S_fixed(EVODR):
    """Ablation: replace LLM-S with a fixed suggestion.
    Always returns the same suggestion regardless of individual quality.
    """

    def _get_f1_evaluation(self, indiv):
        return {
            "evaluation": "Standard evaluation.",
            "suggestion": SUGGESTIONS[0]
        }
