# EvoDR: Evolving Dispatching Rules via Large Language Model for Dynamic Flexible Assembly Flow Shop Scheduling

[![IEEE TEVC](https://img.shields.io/badge/IEEE%20TEVC-2026-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.0.0-green.svg)](https://github.com/jhqiu1/EvoDR/releases)
[![arXiv](https://img.shields.io/badge/arXiv-2601.15738-b31b1b.svg)](https://arxiv.org/abs/2601.15738)
[![中文](https://img.shields.io/badge/中文-README-ff69b4.svg)](README_CN.md)

**EvoDR** uses LLMs to automatically design dispatching rules for dynamic flexible assembly flow shops. Orders keep arriving on the fly; each order contains multiple products, and it only ships when every part and product is ready. EvoDR puts two LLMs to work: one writes the rules, and a scheduling expert (**LLM-S**) reads the evolving population, tells what works and what doesn't, and points out where to go next.

This idea — pairing a code-generating LLM with a domain-expert LLM that turns search results into actionable guidance — is not tied to this problem. It carries over to other complex scheduling problems, and to algorithm design in general: the simulator decides who survives, the expert decides what to try next.

📄 [IEEE Transactions on Evolutionary Computation, 2026](https://arxiv.org/abs/2601.15738)

<p align="center"><img src="docs/figures/framework.png" width="95%" alt="EvoDR framework"></p>

## 📖 How It Works

**Start from an expert rule, not from scratch.** Initialization seeds the population from a classical rule (EDD): LLM-S analyzes its strengths and weaknesses in the current environment, and the first generation is built around those findings.

**Evolve with four operators.** C1 merges the strengths of two parent rules; C2 asks for something completely different; M1 turns LLM-S's suggestions into code changes; M2 retunes the parameters of a good rule. Together they balance exploitation and exploration in language space, not in a fixed symbol space like GP.

**Let the expert talk, not rule.** LLM-S evaluates rules against the dynamic state of the shop and the best/worst performers in the population, then returns structured suggestions. Scores from the simulator decide selection; suggestions only decide what gets generated next.

## 🏆 Results

- On 20 industrial instances, rules evolved by EvoDR outperform GP, GEP, RandSample, FunSearch, EOH, MCTS-AHD, and ReEvo — average tardiness 3.17–16.81% lower, +18.63% over EDD on the test set.
- Across 480 instances in 24 scenarios (line configurations 3+6 to 5+12, arrival volumes 20–50, load factors 1–4), EvoDR stays best or near-best throughout, with an overall ARI of 35.62% over EDD.
- The whole offline design costs about $0.189 with GPT-4o-mini. Once a rule is deployed, there are no LLM calls at all — one priority ranking per decision, sub-millisecond.

<p align="center"><img src="docs/figures/convergence_analysis.png" width="75%" alt="Convergence analysis"></p>
<p align="center">Each drop is an accepted improvement guided by LLM-S feedback: 7371.61 vs. EDD's 8909.21 within 200 samples.</p>

## 📐 Problem Scale

Per instance: 30–60 orders (20–50 arriving dynamically), 39–110 products, 117–355 jobs in total, 9–17 assembly lines, and 577–3253 feasible job–machine pairs to rank at every decision step.

## ⚡ Quick Start

```bash
pip install -r requirements.txt
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"
cd example/online_fafsp
python run_evodr.py
```

This runs the full loop on the bundled 20-instance dataset. To bring EvoDR to your own problem, follow [`EVODR.md`](EVODR.md): define the state features, the action space, and what your domain expert should look at.

## 🔖 Citation

```bibtex
@article{qiu2026evodr,
  title={EvoDR: Evolving Dispatching Rules via Large Language Model for Dynamic Flexible Assembly Flow Shop Scheduling},
  author={Qiu, Junhao and Zhuang, Haoyang and Liu, Fei and Liu, Jianjun and Zhang, Qingfu},
  journal={IEEE Transactions on Evolutionary Computation},
  year={2026},
  note={arXiv:2601.15738}
}
```

Related work from our group: [E2OC](https://github.com/jhqiu1/E2OC) (operator co-design for MOEAs), [LLM4AD](https://github.com/Optima-CityU/LLM4AD) (platform).

Questions or issues: [junhaoqiu2-c@my.cityu.edu.hk](mailto:junhaoqiu2-c@my.cityu.edu.hk)

## 📜 License

MIT. See [LICENSE](LICENSE).
