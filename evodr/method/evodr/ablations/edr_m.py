from ..evodr import EVODR


class EDR_M(EVODR):
    """Ablation: remove mutation operators (m1, m2).
    Only crossover operators (e1, e2) remain.
    """

    def _get_op_list(self):
        return ['e1', 'e2']
