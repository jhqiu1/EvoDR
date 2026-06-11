# EVODR Problem Migration Guide

## Overview

This guide explains how to adapt the EVODR (Evolutionary of Heuristics with Dynamic Rules) method from the Online FAFSP problem to a new optimization problem. It covers both file structure changes and parameter modifications at the code level.

---

## Part 1: File and Folder Replacement

This section identifies which folders and scripts need to be modified when migrating to a new problems.

### 1. Replace Elite Rule for Population Initialization

**Folder/Script to modify**: `llm4/method/evodr/evodr.py`

- **Exact Location**: Method `_get_edd_function()` 
- **Related Method**: `_init_edd_baseline()` 

- This elite rule is the first individual added to the population for initialization

### 2. Replace Evaluation Method

**Folder/Script to modify**: Create a new folder under `llm4/task/optimization/` for your problem

- Current example: `llm4/task/optimization/online_fafsp/`
- You need to:
  1. Create a new folder structure similar to `online_fafsp`
  2. Implement a new `evaluation.py` file with your problem's evaluation logic
  3. This is the most critical part when changing problems

### 3. Replace LLM Generation Content Template

**Folder/Script to modify**: Your problem task folder

- **File**: `template.py` (located under your specific problem folder like `online_fafsp/template.py`)
- Contains:
  - `template_program`: The function signature and feature parameters for LLM-generated code
  - `task_description`: Natural language description of your optimization problem
- This defines what inputs the LLM has access to when generating priority rules

### 4. Replace Prompts and LLM Role Definitions

**Folder/Script to modify**: `llm4/method/evodr/`

- **Files**:
  - `sampler.py`: Contains LLM-A and LLM-S role descriptions
    - `role_description_A`: Algorithm Expert role (code generation)
    - `role_description_S`: Scheduling/Domain Expert role (evaluation)
  - `prompt.py`: Contains all operator prompts (I1, E1, E2, M1, M2, F1, IS1, IA1)
- These define how the LLM interacts with your specific problem domain

---

## Part 2: Parameter Modification 

This section provides specific code locations for modifying key EVODR parameters.

### 1. Temperature Parameters

**File**: `llm4/method/evodr/evodr.py`

**Location**: In the `__init__` method

```python
# Current settings (around line 112-114 in evodr.py)
self._min_u = 1.0  # Minimum temperature
self._max_u = 1.0  # Maximum temperature (currently fixed to 1.0)
self._best_temperature = 1.0  # Best temperature found during initialization
```

**Modification Guide**:

- To enable dynamic temperature variation (linear increase/decrease during initialization):
  ```python
  self._min_u = 0.5   # Lower bound of temperature range
  self._max_u = 2.0   # Upper bound of temperature range
  ```
- Higher temperatures = more randomness in LLM output
- Lower temperatures = more focused, deterministic output

### 2. Iteration and Sampling Parameters

**File**: `example/online_fafsp/run_evodr.py` (or your problem's run script)

**Location**: EVODR initialization 

```python
evodr = EVODR(
    llm=llm,
    evaluation=evaluation,
    profiler=profiler,
    
    # Number of evolutionary generations
    max_generations=20,        # Total generations to run
    
    # Maximum number of samples (LLM calls)
    max_sample_nums=200,       # Stop after this many samples
    
    # Population size
    pop_size=6,                # Number of individuals kept in population
    
    # Selection parameters
    selection_num=2,           # Number of individuals selected for crossover
    
    # ... other parameters
)
```

### 3. Population and Parallelization Parameters

**File**: `example/online_fafsp/run_evodr.py`

**Location**: Same EVODR initialization

```python
evodr = EVODR(
    # ... previous parameters
    
    # Operator toggles
    use_e1_operator=True,      # Enable/disable crossover operator E1
    use_e2_operator=True,      # Enable/disable crossover operator E2
    use_m1_operator=True,      # Enable/disable mutation operator M1
    use_m2_operator=True,      # Enable/disable mutation operator M2
    
    # Parallelization settings
    num_samplers=2,            # Number of sampling threads
    num_evaluators=10,         # Number of evaluation threads/processes
    
    # ... other parameters
)
```

### 4. Initialization Population Size

**File**: `llm4/method/evodr/evodr.py`

**Location**: In the `__init__` method (look for `initial_sample_nums_max`)

```python
# Search for this parameter (around line 100-110)
self._initial_sample_nums_max = 10  # Number of individuals for initialization phase
```

### 5. Evaluation Timeout

**File**: `example/online_fafsp/run_evodr.py`

**Location**: Evaluation initialization

```python
evaluation = Online_fafsp_Evaluation(
    timeout_seconds=20,        # Evaluation timeout per LLM-generated program
    n_instance=16,             # Number of problem instances for evaluation
    n_jobs=50,                 # Problem-specific: number of jobs
    n_machines=10,             # Problem-specific: number of machines
)
```

---

## Quick Start for New Problem

1. **Create new task folder** under `llm4/task/optimization/[your_problem]/`
2. **Implement** `evaluation.py` and `template.py` for your problem
3. **Create run script** similar to `example/online_fafsp/run_evodr.py`
4. **Adjust parameters** in the run script based on your problem's needs
5. **Modify LLM roles/prompts** in `sampler.py` and `prompt.py` if needed
6. **Adjust temperature range** in `evodr.py` if dynamic temperature is desired