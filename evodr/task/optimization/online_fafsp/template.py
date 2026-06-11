template_program = '''
import numpy as np

def cal_priority(
    status: int,
    num_neighboring_machine: int,
    processing_time: float,
    start_time: float,
    delivery_time: float,
    available_time: float,
    num_neighboring_operation: int,
    utilization: float,
    processing_tm: float,
) -> float:
    """
    Calculate priority for job-machine arcs using multi-factor heuristic optimization.
    This algorithm considers job urgency, machine availability, and processing efficiency
    to minimize tardiness in dynamic flexible assembly shop scheduling.

    Args:
        status (int): Job status (0-ready, 1-in progress)
        num_neighboring_machine (int): Number of compatible machines
        processing_time (float): Actual processing time required
        start_time (float): Estimated start time
        delivery_time (float): Job due date (critical for EDF principle)
        available_time (float): Machine's next available time
        num_neighboring_operation (int): Number of processable operations
        utilization (float): Machine utilization rate [0-1]
        processing_tm (float): Actual processing time on this machine

    Returns:
        float: Priority value (smaller values indicate higher priority)
    """

    # Prioritization by delivery time (smaller delivery_time = higher priority)
    priority = delivery_time

    # Return priority results
    return priority
'''

task_description = """
Design a priority calculation algorithm for job-machine assignments in a dynamic shop scheduling environment. The scenario involves 10 initial orders at time zero, with 20 additional orders arriving according to an exponential distribution (mean arrival interval = average order processing time / shop load factor of 0.85). The optimization objective is to minimize total tardiness. The algorithm should comprehensively consider factors such as job delivery urgency, machine availability, and processing efficiency to compute a priority value for each job-machine combination, adhering to the convention that a smaller numerical value indicates higher priority.
"""

#
