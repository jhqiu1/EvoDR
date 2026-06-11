


from __future__ import annotations
from typing import Any, List, Tuple, Callable
import numpy as np
import matplotlib.pyplot as plt
import concurrent.futures

import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
    )
)


from evodr.base import Evaluation

import inspect
import textwrap
from evodr.task.optimization.online_fafsp.schedule import Sched
from evodr.task.optimization.online_fafsp.get_instance import load_data

from evodr.task.optimization.online_fafsp.template import (
    template_program,
    task_description,
)


__all__ = ["Online_fafsp_Evaluation"]


def _eval_single_instance(args):
    """Module-level helper for parallel instance evaluation (picklable)."""
    instance, code = args
    from evodr.task.optimization.online_fafsp.schedule import Sched
    sche = Sched(instance, "LLM")
    return sche.schedule(code)


class Online_fafsp_Evaluation(Evaluation):
    """Evaluator for dynamic Job Shop Scheduling Problem."""

    def __init__(
        self, timeout_seconds=100, n_instance=16, n_jobs=50, n_machines=10, **kwargs
    ):
        """
        Args:
            None
        Raises:
            AttributeError: If the data key does not exist.
            FileNotFoundError: If the specified data file is not found.
        """
        super().__init__(
            template_program=template_program,
            task_description=task_description,
            use_numba_accelerate=False,
            timeout_seconds=timeout_seconds,
        )

        self.n_instance = n_instance
        self.n_jobs = n_jobs
        self.n_machines = n_machines
        # getData = GetData(self.n_instance, self.n_jobs, self.n_machines)
        # txt = "m13-m26-f0.5-arrive20-u1.txt"
        txt = "m13-m26-f0.5-arrive20-u1.txt"
        # txt = '100-20-4.txt'
        # file = r"./data_test/" + txt
        self._txt = txt  # expose filename for parameter extraction
        Datas = load_data(txt)
        self._datasets = Datas

    def evaluate_program(self, program_str: str, callable_func: Callable) -> Any | None:
        return self.evaluate(str(program_str))

    def evaluate(self, eva) -> float:
        """
        Evaluate the constructive heuristic for online fafsp.


        Returns:
            The average makespan across all instances.
        """

        code = eva

        delays = []
        n_workers = min(4, len(self._datasets))
        instances = list(self._datasets.items())

        # Parallel evaluation across instances using multi-processing
        try:
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as pool:
                tasks = [(inst, code) for _, inst in instances]
                delays = list(pool.map(_eval_single_instance, tasks))
        except Exception:
            print("[WARN] 多进程评估失败，回退到串行评估")
            # Fallback to serial evaluation on failure (e.g., Windows spawn error)
            for _, instance in instances:
                sche = Sched(instance, "LLM")
                delays.append(sche.schedule(code))

        average_delay = np.mean(delays)
        return -average_delay  # Negative because we want to minimize the makespan

    def evaluate_program_fromResult(
        self, program_str: str, callable_func: Callable
    ) -> Any | None:

        code = callable_func

        delays = {}
        # for i in range(10):
        #     instance = self._datasets[i]
        #     sche = Sched(instance, "LLM")
        #     delay = sche.schedule(code)
        #     delays.append(delay)

        for _, instance in self._datasets.items():
            sche = Sched(instance, "LLM")
            delay = sche.schedule(code)
            delays[sche.data.xlsx_file] = -delay

        # average_delay = np.mean(delays)
        return delays


# 转换为可调用函数
def string_to_callable(function_string, function_name=None):
    """
    将函数定义字符串转换为可调用函数对象

    参数:
        function_string: 包含函数定义的字符串
        function_name: 可选，要提取的函数名称。如果未提供，则从字符串中自动提取

    返回:
        可调用的函数对象，如果转换失败则返回None
    """
    try:
        # 创建新的命名空间并导入必要的模块
        namespace = {}

        # 导入代码中可能需要的常用模块
        try:
            import numpy as np

            namespace["np"] = np
        except ImportError:
            print("Warning: numpy not available")

        try:
            from typing import Tuple, List, Dict, Any, Union, Optional

            namespace["Tuple"] = Tuple
            namespace["List"] = List
            namespace["Dict"] = Dict
            namespace["Any"] = Any
            namespace["Union"] = Union
            namespace["Optional"] = Optional
        except ImportError:
            print("Warning: typing module not available")

        # 执行代码字符串
        exec(function_string, namespace)

        # 提取函数名（如果未提供）
        if function_name is None:
            # 从字符串中提取函数名
            lines = function_string.strip().split("\n")
            for line in lines:
                if line.startswith("def "):
                    function_name = line.split("def ")[1].split("(")[0].strip()
                    break

        # 获取函数引用
        callable_func = namespace.get(function_name)

        if callable_func is not None and callable(callable_func):
            return callable_func
        else:
            print(
                f"Warning: Function '{function_name}' not found or not callable in code"
            )
            return None

    except Exception as e:
        print(f"Error converting string to callable: {e}")
        return None


if __name__ == "__main__":

    # def cal_priority(
    #     status,
    #     num_neighboring_machine,
    #     processing_time,
    #     start_time,
    #     delivery_time,
    #     available_time,
    #     num_neighboring_operation,
    #     utilization,
    #     processing_tm,
    # ):
    #     # {This new algorithm prioritizes jobs and machines based on completion urgency, cost-effectiveness of processing, and machine availability, using different weighting factors to promote efficient scheduling.}

    #     priority = 0

    #     # Assess urgency based on delivery time; shorter remaining time increases priority
    #     if delivery_time > 0:
    #         priority += delivery_time * 3  # Moderate weight for urgency

    #     # Incorporate processing time as a penalty; longer times will lower priority
    #     if processing_time > 0:
    #         priority -= processing_time * 1.5  # Lesser impact from processing time

    #     # Adjust for machine availability; scarce available time increases priority
    #     if available_time > 0:
    #         priority += 1 / available_time  # Higher priority for less available time
    #     else:
    #         priority += 1e6  # Heavy penalty for no availability

    #     # Penalize based on neighboring machines; more neighbors generally decrease priority
    #     priority -= num_neighboring_machine * 1.0

    #     # Consider utilization; higher utilization means greater risk of delays
    #     if utilization > 0:
    #         priority += utilization * 30  # Moderate impact based on utilization

    #     # Factor in time already processed on the machine; previously loaded machines increase priority
    #     if processing_tm > 0:
    #         priority += processing_tm * 0.3  # Lesser impact from previous loads

    #     # Adjust for job status; scheduling readiness boosts priority
    #     if status == 0:
    #         priority *= 0.9  # Slight increase for ready-to-schedule jobs

    #     # Evaluate the dynamic impact of job start delays; greater delays lead to heavier penalties
    #     delay_penalty = (
    #         (start_time - delivery_time) * 2 if start_time > delivery_time else 0
    #     )
    #     priority += delay_penalty

    #     # Integrate previous operational efficiency; balance workload over the number of operations
    #     if num_neighboring_operation > 0:
    #         efficiency_adjustment = (processing_time / num_neighboring_operation) * 5
    #         priority -= efficiency_adjustment
    #     else:
    #         priority -= 0  # Zero operations imply no adjustment

    #     return priority
    # def cal_priority(
    #     status,
    #     num_neighboring_machine,
    #     processing_time,
    #     start_time,
    #     delivery_time,
    #     available_time,
    #     num_neighboring_operation,
    #     utilization,
    #     processing_tm,
    # ):
    #     """
    #     Calculate priority for job-machine arcs using multi-factor heuristic optimization.
    #     This algorithm considers job urgency, machine availability, and processing efficiency
    #     to minimize tardiness in dynamic flexible assembly shop scheduling.

    #     Args:
    #         status (int): Job status (0-ready, 1-in progress)
    #         num_neighboring_machine (int): Number of compatible machines
    #         processing_time (float): Actual processing time required
    #         start_time (float): Estimated start time
    #         delivery_time (float): Job due date (critical for EDF principle)
    #         available_time (float): Machine's next available time
    #         num_neighboring_operation (int): Number of processable operations
    #         utilization (float): Machine utilization rate [0-1]
    #         processing_tm (float): Actual processing time on this machine

    #     Returns:
    #         float: Priority value (smaller values indicate higher priority)
    #     """

    #     # Prioritization by delivery time
    #     priority = delivery_time

    #     # Return priority results
    #     return priority
    from template import template_program
    import inspect

    cal_priority = string_to_callable(template_program, "cal_priority")
    # string = inspect.getsource(cal_priority)
    print("函数代码如下：")
    # print(string)

    tsp = Online_fafsp_Evaluation()
    delay = tsp.evaluate_program("_", cal_priority)
    print(delay)
