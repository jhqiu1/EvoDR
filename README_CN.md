# EvoDR：基于大语言模型的动态柔性装配流水车间调度规则自动设计

[![IEEE TEVC](https://img.shields.io/badge/IEEE%20TEVC-2026-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.0.0-green.svg)](https://github.com/jhqiu1/EvoDR/releases)
[![arXiv](https://img.shields.io/badge/arXiv-2601.15738-b31b1b.svg)](https://arxiv.org/abs/2601.15738)
[![English](https://img.shields.io/badge/English-README-blue.svg)](README.md)

**EvoDR** 用 LLM 自动设计动态柔性装配流水车间的调度规则。订单持续到达，每个订单包含多个产品，要所有部件和产品全部齐套才能交付。框架里有两个 LLM 各司其职：一个写规则，另一个调度专家（**LLM-S**）盯着进化中的种群，指出哪好哪不好、下一步该往哪走。

这个思路——让写代码的 LLM 和懂领域的 LLM 配对，把搜索结果翻译成可执行的引导——并不绑定在这一个问题上。它可以搬到其他复杂排产问题，也可以搬到一般的算法设计任务：模拟器决定谁留下，领域专家决定接下来试什么。

📄 [IEEE Transactions on Evolutionary Computation, 2026](https://arxiv.org/abs/2601.15738)

<p align="center"><img src="docs/figures/framework.png" width="95%" alt="EvoDR 框架图"></p>

## 📖 工作原理

**从专家规则出发，不从零开始。** 初始化以经典规则（EDD）为种子：LLM-S 分析它在当前环境下的优劣势，第一代种群围绕这些发现生成。

**四个算子进化。** C1 融合两个父代规则的长处；C2 要求生成和现有规则完全不同的东西；M1 把 LLM-S 的建议落成代码改动；M2 在好规则上调参数。探索与利用的平衡发生在语言空间里，而不是 GP 那种固定符号空间。

**让专家说话，但不让专家掌权。** LLM-S 结合车间动态状态和种群里最好/最差的表现来评估规则，返回结构化建议。模拟器算的分数决定选择，建议只决定下一代生成什么。

## 🏆 结果

- 20 个工业实例上，EvoDR 进化出的规则优于 GP、GEP、RandSample、FunSearch、EOH、MCTS-AHD 和 ReEvo——平均拖期低 3.17–16.81%，测试集上比 EDD 高 18.63%。
- 480 个实例、24 个工况（产线从 3+6 到 5+12、到达订单 20–50、负载因子 1–4），EvoDR 始终保持最优或接近最优，总体相对 EDD 的 ARI 为 35.62%。
- 整个离线设计用 GPT-4o-mini 只花约 $0.189。规则部署后完全不调 LLM——每个决策步做一次优先级排序，亚毫秒。

<p align="center"><img src="docs/figures/convergence_analysis.png" width="75%" alt="收敛分析"></p>
<p align="center">每一次下降都是一次被 LLM-S 反馈引导的改进：200 次采样内做到 7371.61，EDD 为 8909.21。</p>

## 📐 问题规模

单个算例：30–60 个订单（其中 20–50 个动态到达）、39–110 个产品、共 117–355 个作业、9–17 条产线，每个决策步要对 577–3253 个可行的作业–产线配对排序。

## ⚡ 快速开始

```bash
pip install -r requirements.txt
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"
cd example/online_fafsp
python run_evodr.py
```

这会在内置的 20 实例数据集上跑完整流程。想把 EvoDR 搬到自己的问题上，看 [`EVODR.md`](EVODR.md)：定义好状态特征、动作空间，以及你的领域专家该看什么。

## 🔖 引用

```bibtex
@article{qiu2026evodr,
  title={EvoDR: Evolving Dispatching Rules via Large Language Model for Dynamic Flexible Assembly Flow Shop Scheduling},
  author={Qiu, Junhao and Zhuang, Haoyang and Liu, Fei and Liu, Jianjun and Zhang, Qingfu},
  journal={IEEE Transactions on Evolutionary Computation},
  year={2026},
  note={arXiv:2601.15738}
}
```

我们组的其他工作：[E2OC](https://github.com/jhqiu1/E2OC)（多目标进化算法的算子协同设计）、[LLM4AD](https://github.com/Optima-CityU/LLM4AD)（平台）。

有问题或建议：[junhaoqiu2-c@my.cityu.edu.hk](mailto:junhaoqiu2-c@my.cityu.edu.hk)

## 📜 许可证

MIT，见 [LICENSE](LICENSE)。
