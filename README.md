# EvoDR

Code for "EvoDR: Evolving Dispatching Rules via Large Language Model for Dynamic Flexible Assembly Flow Shop Scheduling".

> **Note:** This repository contains a partial implementation for review purposes.  
> The complete codebase (including baseline methods, ablation scripts, and robustness evaluation) will be released upon paper acceptance.

## Repository Structure

```
evodr/
├── base/               # Core utilities (code parsing, evaluation, LLM interface)
├── method/evodr/       # EvoDR algorithm implementation
│   ├── evodr.py        # Main algorithm (dual-expert co-evolution)
│   ├── population.py   # Population management
│   ├── prompt.py       # Prompt templates for operators (C1/C2/M1/M2/F1)
│   ├── prompt_algo.py  # LLM-A task description and input/output definitions
│   ├── prompt_sche.py  # LLM-S evaluation prompt design
│   ├── sampler.py      # LLM sampling and response parsing
│   ├── profiler.py     # Experiment logging
│   └── ablations/      # Ablation variants
├── task/optimization/online_fafsp/  # Scheduling simulator
│   ├── schedule.py     # Event-driven scheduler
│   ├── state.py        # System state (heterogeneous graph MDP)
│   ├── evaluation.py   # Fitness evaluation
│   ├── get_instance.py # Data loading
│   ├── heuristic.py    # Classical PDR baselines
│   └── template.py     # PDR code template
└── tools/              # Utilities
    ├── llm/            # LLM API wrappers (OpenAI, vLLM, Ollama)
    └── profiler/       # Logging profilers

example/online_fafsp/
├── run_evodr.py        # Main run script
└── data_test/          # Small-scale test instance
```

## Requirements

- Python >= 3.10
- numpy, pandas, scipy, matplotlib, PyYAML
- openai (for GPT-4o-mini or other OpenAI-compatible APIs)

Install:
```bash
pip install -r requirements.txt
```

## Quick Start

1. **Set your LLM credentials** (via environment variables):
```bash
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"
```

2. **Run EvoDR**:
```bash
cd example/online_fafsp
python run_evodr.py
```
