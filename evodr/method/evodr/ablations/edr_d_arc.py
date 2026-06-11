from ..evodr import EVODR


class EDR_D_arc(EVODR):
    """Ablation: remove J-M arc feature (index 8).
    Disables: processing_tm.
    """

    def _get_feature_mask(self):
        return [True, True, True, True, True, True, True, True, False]
