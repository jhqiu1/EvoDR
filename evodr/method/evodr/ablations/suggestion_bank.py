"""Generic suggestion pool for the EDR-S ablation variants.

This small pool (4 generic suggestions) backs the EDR-S(fix) and EDR-S(random)
variants in the ablation study (Table VI of the paper). The paper's revision
additionally reports a controlled study with an enlarged generic pool (37
items) and a structured pool (17 items); see the response to Reviewer #2,
Comment 1.
"""

SUGGESTIONS = [
    "Prioritize jobs with earlier delivery times to reduce tardiness.",
    "Assign jobs to machines with shorter processing times to minimize queue time.",
    "Consider machine utilization when scheduling to balance workload across machines.",
    "Factor in job arrival patterns and available machine capacity for dynamic scheduling.",
]
