from ..evodr import EVODR
from ..prompt_algo import Prompt_algo
from ..prompt_sche import Prompt_sche
from ..prompt import EVODRPrompt


class StaticPromptAlgo(Prompt_algo):
    """Prompt_algo variant without dynamic environment description (for EDR-DE)."""

    def __init__(self):
        self.prompt_task = (
            "Design a priority calculation algorithm for job-machine assignments "
            "in a shop scheduling environment, with the optimization goal of "
            "minimizing tardiness. The output priority value should follow "
            "smaller-value-higher-priority convention."
        )
        self.prompt_func_name = "cal_priority"
        self.prompt_func_inputs = [
            "status", "num_neighboring_machine", "processing_time",
            "start_time", "delivery_time", "available_time",
            "num_neighboring_operation", "utilization", "processing_tm"
        ]
        self.prompt_func_outputs = ["priority"]
        self.prompt_inout_inf = (
            "The 'job' variable represents job-related information including "
            "status (0/1 indicating scheduling status), num_neighboring_machine "
            "(number of compatible machines), processing_time (actual/average "
            "processing time), start_time (actual/estimated start time), and "
            "delivery_time (actual delivery time). The 'machine' variable "
            "contains machine-related data such as available_time (machine's "
            "next available time), num_neighboring_operation (number of "
            "processable operations), and utilization (machine utilization "
            "rate [0-1]). The 'J-M Arc' variable represents the association "
            "of a job with a device, including processing_tm (actual processing "
            "time on machine). The output 'priority' stores numerical priority "
            "values where lower values indicate higher priority."
        )
        self.prompt_other_inf = (
            "All input variables may have a value of zero. Therefore, when "
            "division occurs, you need to determine whether the divisor is 0 "
            "or not. The generated code needs to be ensured that there are no "
            "syntax errors, invalid syntax and logic errors."
        )


class StaticPromptSche(Prompt_sche):
    """Prompt_sche variant without dynamic environment description (for EDR-DE)."""

    def get_introd(self):
        return ""


class EDR_DE(EVODR):
    """Ablation: remove dynamic environment description from prompts.
    Replaces the dynamic problem context (order count, arrival distribution,
    load factor) with a static generic description.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        static_algo = StaticPromptAlgo()
        EVODRPrompt.prompt_algo = static_algo
        EVODRPrompt.prompt_sche = StaticPromptSche(10, 20, 1)
        # Also update the instance-level task description (used by 6/8 prompt generators)
        self._task_description_str = static_algo.get_task()
