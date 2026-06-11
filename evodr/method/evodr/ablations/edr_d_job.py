from ..evodr import EVODR


class EDR_D_job(EVODR):
    """Ablation: remove job features (indices 0-4).
    Disables: status, num_neighboring_machine, processing_time, start_time, delivery_time.
    """

    def _get_feature_mask(self):
        # [status, num_mach, proc_time, start_time, delivery, avail, num_oper, util, proc_tm]
        return [False, False, False, False, False, True, True, True, True]
