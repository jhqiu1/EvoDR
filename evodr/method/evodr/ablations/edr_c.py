from ..evodr import EVODR


class EDR_C(EVODR):
    """Ablation: remove crossover operators (e1, e2).
    Only mutation operators (m1, m2) remain.
    """

    def _get_op_list(self):
        return ['m1', 'm2']
