from ..evodr import EVODR


class EDR_D_machine(EVODR):
    """Ablation: remove machine features (indices 5-7).
    Disables: available_time, num_neighboring_operation, utilization.
    """

    def _get_feature_mask(self):
        return [True, True, True, True, True, False, False, False, True]
