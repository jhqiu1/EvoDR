from ..evodr import EVODR


class EDR_S_none(EVODR):
    """Ablation: remove LLM-S entirely.
    No F1 evaluation feedback — evolution driven purely by numerical fitness.
    """

    def _should_use_f1_evaluation(self):
        return False
