from ..evodr import EVODR


class EDR_E(EVODR):
    """Ablation: remove elite knowledge initialization.
    No EDD baseline — all initial individuals are generated from scratch via ia2.
    """

    def _should_init_edd_baseline(self):
        return False
