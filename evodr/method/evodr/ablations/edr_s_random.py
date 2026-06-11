import random
from ..evodr import EVODR
from .suggestion_bank import SUGGESTIONS


class EDR_S_random(EVODR):
    """Ablation: replace LLM-S with a random suggestion.
    Randomly selects a suggestion from the predefined bank.
    """

    def _get_f1_evaluation(self, indiv):
        return {
            "evaluation": "Standard evaluation.",
            "suggestion": random.choice(SUGGESTIONS)
        }
