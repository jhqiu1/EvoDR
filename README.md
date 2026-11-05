<div align="center">

# ⚡ EvoDR

### A scheduling expert that designs its own dispatching rules.

**Evolving rules in language space, not symbol trees.**

[![IEEE TEVC](https://img.shields.io/badge/IEEE%20TEVC-2026-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.0.0-green.svg)](https://github.com/jhqiu1/EvoDR/releases)
[![arXiv](https://img.shields.io/badge/arXiv-2601.15738-b31b1b.svg)](https://arxiv.org/abs/2601.15738)
[![中文](https://img.shields.io/badge/中文-README-ff69b4.svg)](README_CN.md)

</div>

Orders land by the minute. Each one ships only when every part and every product is ready. Designing dispatching rules for this by hand is a losing game — and GP-style automatic design is stuck searching symbol trees.

**EvoDR sends two LLMs after the problem:**

> 🧠 **One writes rules. One runs the shop floor.**
> LLM-A generates executable rules. **LLM-S**, a scheduling expert, reads the population, spots what's working and what's dead weight, and steers the next generation.
>
> *The simulator decides who survives. The expert decides what to try next.*

The rules that come out run in **sub-milliseconds**, call **zero LLMs**, and cost **$0.189** to design.

<div align="center">

| 🏆 Beats 7 AHD baselines | 📊 480 instances · 24 scenarios | 💸 $0.189 per design | ⚡ <1 ms per decision |
|---|---|---|---|

</div>

📄 **[IEEE Transactions on Evolutionary Computation, 2026](https://arxiv.org/abs/2601.15738)**

<p align="center"><img src="docs/figures/framework.png" width="95%" alt="EvoDR framework"></p>

## 🧠 The Idea

Every LLM-based algorithm design loop we know asks the model for *code*. EvoDR asks for something extra: **judgment.** A second, domain-expert LLM watches the search, reads the best and worst rules, and turns raw fitness numbers into semantic guidance — "this rule starves the assembly stage," "that weight is doing nothing." 

That guidance never touches selection; it only shapes what gets generated next. The pattern drops into any LLM-driven algorithm design loop, on any complex scheduling or optimization problem.

## ⚙️ The Loop

- 🔥 **Cold start from EDD** — LLM-S dissects a classical rule, and generation 1 is built around its weaknesses
- 🔀 **Four operators** — C1 fuses parent strengths · C2 demands something entirely new · M1 codes up LLM-S's suggestions · M2 retunes the weights
- 🏁 **Deploy and forget** — the evolved rule is a single priority function: 577–3253 job–machine pairs ranked per decision step, no model in the loop

<p align="center"><img src="docs/figures/convergence_analysis.png" width="75%" alt="Convergence analysis"></p>
<p align="center"><em>Every drop is a rule improvement steered by the expert: 7371.61 vs. EDD's 8909.21, within 200 samples.</em></p>

## 📊 The Numbers

| Arena | Result |
|---|---|
| vs. GP · GEP · RandSample · FunSearch · EOH · MCTS-AHD · ReEvo (20 industrial instances) | **3.17–16.81%** lower avg. tardiness, +18.63% over EDD on test |
| Robustness: 24 scenarios, 480 instances (3+6 → 5+12 lines, 20–50 arrivals, load 1–4×) | Best or near-best throughout, **ARI 35.62%** over EDD |
| One full design run (GPT-4o-mini) | **$0.189**, 0.46M tokens |
| Online dispatching | **< 1 ms**, zero LLM calls |
| Significance | Friedman + Wilcoxon, all p ≤ 0.0025 (Bonferroni) |

## 🚀 Quick Start

```bash
pip install -r requirements.txt
export LLM_API_KEY="your-api-key" LLM_BASE_URL="https://api.openai.com/v1" LLM_MODEL="gpt-4o-mini"
cd example/online_fafsp && python run_evodr.py
```

Bring EvoDR to your own problem: define the state, the actions, and what your domain expert should look at — [`EVODR.md`](EVODR.md) walks you through it.

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

More from the group: [E2OC](https://github.com/jhqiu1/E2OC) · [LLM4AD](https://github.com/Optima-CityU/LLM4AD) · [junhaoqiu2-c@my.cityu.edu.hk](mailto:junhaoqiu2-c@my.cityu.edu.hk)

## 📜 License

MIT — see [LICENSE](LICENSE).
