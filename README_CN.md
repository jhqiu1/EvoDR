# EvoDR：基于大语言模型的动态柔性装配流水车间调度规则自动演化

[![IEEE TEVC](https://img.shields.io/badge/IEEE%20TEVC-2026-blue)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.0.0-green.svg)](https://github.com/jhqiu1/EvoDR/releases)
[![arXiv](https://img.shields.io/badge/arXiv-2601.15738-b31b1b.svg)](https://arxiv.org/abs/2601.15738)
[![English](https://img.shields.io/badge/English-README-blue.svg)](README.md)

**EvoDR** 面向带**双成套约束**（部件齐套 + 多产品整单齐套交付）的**动态柔性装配流水车间调度问题（FAFSP）**，自动演化优先调度规则（PDR）。核心思想：**在模拟器返回的目标适应度之外，额外引入调度专家 LLM（LLM-S）提供结构化语义引导**（规则分析、局限与改进方向），用于引导规则生成——适应度仍是选择的唯一依据，语义反馈只引导生成。这一「适应度负责选择、领域语义负责引导」的双通道模式不限于 FAFSP，可推广到其他复杂排产问题乃至一般算法设计任务。

📄 论文：[IEEE Transactions on Evolutionary Computation, 2026](https://arxiv.org/abs/2601.15738) · 预印本：[arXiv:2601.15738](https://arxiv.org/abs/2601.15738)

> 本仓库包含 EvoDR 核心框架与一个可直接运行的 FAFSP 算例。对比的 AHD 基线方法（GP/GEP/FunSearch/EOH/MCTS-AHD/ReEvo）与鲁棒性实验数据（24 个工况）未包含。`ablations/` 目录包含论文消融实验的 EDR-S 系列变体，其中的小建议池（4 条通用建议）即论文 Table VI 所用版本。

## 📖 简介

### 🎨 设计范式

1. 👤 **专家规则**（EDD、FIFO+SPT 等）—— 快速、可解释，但对工况高度敏感，高负载下性能急剧退化
2. 🔧 **基于 GP 的自动设计** —— 受限于固定终端符号集，难以利用动态状态语义
3. 🚀 **EvoDR（本文）** —— 在语言空间中协同演化规则与设计知识，自适应动态调度特征

### 🏗️ EvoDR 框架

- 🔥 **精英知识引导初始化**：LLM-S 分析精英规则（EDD），将其优势、局限与改进方向注入初始种群。
- 🧠 **双专家协同进化**：LLM-A 依据 C1/C2/M1/M2 算子提示生成 PDR；LLM-S 结合动态特征与种群上下文给出结构化建议。
- ⚖️ **混合评估**：两条独立通道——模拟器计算的目标适应度（最优解更新、父代与生存选择的唯一依据）与 LLM-S 的语义通道（仅注入下一代生成提示）。
- 🔁 **四个演化算子**：C1 优势融合交叉、C2 探索性交叉、M1 定向优化（由 LLM-S 建议驱动）、M2 参数调优。

<p align="center"><img src="docs/figures/framework.png" width="95%" alt="EvoDR 框架图"></p>
<p align="center"><em>EvoDR 框架总览：初始化、混合评估与协同进化。</em></p>

### 🔭 可推广性

核心机制与具体问题无关：**任何基于 LLM 的算法设计循环，都可以增加一个领域专家 LLM，让它读取种群、把数值结果转化为可执行的语义引导**，而完全不触碰适应度与选择。消融实验表明，LLM-S 的调度专用反馈提供了随机建议（多样性）之外的定向价值。迁移到新问题域（重新定义状态特征、动作空间与领域专家提示）参见 [`EVODR.md`](EVODR.md)。

### 📐 问题与规模

调度决策建模为异构图上可行「作业–设备」配对的优先级排序，由作业完工或订单到达事件触发。单个算例规模：

| 项目 | 范围 |
|---|---|
| 客户订单（含 20–50 个动态到达） | 30–60 |
| 产品（总装作业） | 39–110 |
| 部件任务 | 78–250 |
| 作业总数 | 117–355 |
| 产线（总装 + 部装） | 9–17（3+6 到 5+12） |
| 每个决策步的可行作业–设备配对 | 577–3253 |

### 🏆 主要结果

- **对比 AHD 方法**（GP、GEP、RandSample、FunSearch、EOH、MCTS-AHD、ReEvo；20 个工业实例、每方法 200 次采样）：平均拖期降低 3.17–16.81%；测试集相对 EDD 提升 18.63%；Friedman + Wilcoxon 检验显著（全部 p ≤ 0.0025，Bonferroni 校正）。
- **鲁棒性**（480 实例、24 个工况，覆盖资源规模 / 柔性 / 到达量 / 负载因子）：绝大多数工况取得最优或接近最优；总体平均拖期最低，相对 EDD 的 ARI 为 35.62%。
- **成本**：使用 GPT-4o-mini 的一次离线设计约 $0.189、0.46M tokens；在线调度只需每个决策步一次优先级排序——不调用 LLM，亚毫秒响应。

<p align="center"><img src="docs/figures/convergence_analysis.png" width="75%" alt="收敛分析"></p>
<p align="center"><em>LLM-S 反馈驱动的演化过程：每次下降对应一次被接受的规则改进，200 次采样内达到 7371.61（EDD 为 8909.21）。</em></p>

## 📦 环境依赖

- Python >= 3.10
- `numpy`、`pandas`、`scipy`、`matplotlib`、`PyYAML`
- `openai`（GPT-4o-mini 或其他 OpenAI 兼容接口）

```bash
pip install -r requirements.txt
```

## ⚡ 快速开始

1. **配置 LLM 凭据**：

```bash
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o-mini"
```

2. **运行 EvoDR**：

```bash
cd example/online_fafsp
python run_evodr.py
```

将在内置的 20 实例 FAFSP 数据集（`data_test/m13-m26-f0.5-arrive20-u1.txt`）上执行精英引导初始化与协同进化。迁移到新问题域参见 [`EVODR.md`](EVODR.md)。

## 📁 目录结构

```
evodr/
├── base/               # 基础工具（代码解析、评估、LLM 接口）
├── method/evodr/       # EvoDR 算法实现
│   ├── evodr.py        # 主算法（双专家协同进化）
│   ├── population.py   # 种群管理
│   ├── prompt.py       # 算子提示模板（C1/C2/M1/M2/F1）
│   ├── prompt_algo.py  # LLM-A 任务描述与输入输出定义
│   ├── prompt_sche.py  # LLM-S 评估提示设计
│   ├── sampler.py      # LLM 采样与响应解析
│   ├── profiler.py     # 实验日志
│   └── ablations/      # 消融变体（EDR-C/E/M/DE/D/S 系列）
├── task/optimization/online_fafsp/  # 调度模拟器
│   ├── schedule.py     # 事件驱动调度器
│   ├── state.py        # 系统状态（异构图 MDP，9 维特征）
│   ├── evaluation.py   # 适应度评估
│   ├── get_instance.py # 数据加载
│   ├── heuristic.py    # 经典 PDR 基线
│   └── template.py     # PDR 代码模板
└── tools/
    ├── llm/            # LLM API 封装（OpenAI、vLLM、Ollama）
    └── profiler/       # 日志记录

example/online_fafsp/
├── run_evodr.py        # 主运行脚本
└── data_test/          # 内置数据集（20 实例）
```

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

如果你对基于 LLM 的自动启发式设计感兴趣，也可以看看 [E2OC](https://github.com/jhqiu1/E2OC) 与 [LLM4AD](https://github.com/Optima-CityU/LLM4AD)。

使用中遇到问题，请联系 [junhaoqiu2-c@my.cityu.edu.hk](mailto:junhaoqiu2-c@my.cityu.edu.hk) 或提交 issue。

## 📜 许可证

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE)。
