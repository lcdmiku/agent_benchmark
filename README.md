# Agent Benchmark Research

面向 AI Agent 的能力评测、错误分析与系统改进课程项目。

本项目以 **DeepSeek Harness（DSH）** 为被测 Agent，使用 **Harbor** 作为 Benchmark 运行与评测框架，开展 Agent 能力评测（Evaluation）、错误分析（Error Study）和智能体改进（Agent Improvement）。

## 1. 技术栈

| 组件 | 技术 / 版本 |
|---|---|
| Agent | DeepSeek Harness |
| DSH Runtime | 0.2.2-rc.1 |
| Benchmark Framework | Harbor 0.25.0 |
| Python | 3.12+ |
| Python 环境管理 | uv |
| 容器环境 | Docker Desktop |
| Linux 环境 | WSL2 Ubuntu 24.04 |
| 模型运行方式 | API |

## 2. 项目目标

- **作业一：Benchmark 测试与 Error Study**
  - 选择公开 Benchmark 开展 Agent 能力评测。
  - 记录完整 Execution Trace。
  - 分析典型错误及其产生原因。

- **作业二：Agent 改造与优化**
  - 基于作业一的错误分析提出改进方案。
  - 对 DSH 进行实质性改造。
  - 通过对照实验和消融实验验证改进效果。

- **作业三：Benchmark 构建**
  - 参与小组高质量 Benchmark 设计与验证。

## 3. 环境配置

项目主要在 WSL2 Ubuntu 24.04 中运行。

克隆项目后进入目录：

```bash
cd ~/Agent-Benchmark-Research
```

安装 Python 依赖：

```bash
uv sync
```

激活虚拟环境：

```bash
source .venv/bin/activate
```

检查环境：

```bash
python --version
uv run harbor --version
docker version
dsh --version
```

确保 Docker Desktop 正常运行，并且 WSL2 可以访问 Docker。

## 4. 运行 Smoke Test

目前已经完成 DSH 与 Harbor 的初步集成。

运行 Hello Harbor 测试：

```bash
uv run harbor run \
  --path "$HOME/Agent-Benchmark-Research/harbor-lab/hellow-harbor" \
  --agent harbor_agent.dsh_agent:DSHAgent \
  --env docker \
  --n-concurrent 1 \
  --jobs-dir "$HOME/Agent-Benchmark-Research/runs/harbor-jobs" \
  --job-name hello-harbor-smoke
```

查看实验结果：

```bash
uv run harbor view \
  "$HOME/Agent-Benchmark-Research/runs/harbor-jobs"
```

## 5. 项目目录

```text
Agent-Benchmark-Research/
│
├── configs/                  # 实验配置
│
├── benchmarks/               # Benchmark 数据与配置
│
├── harbor_agent/              # 自定义 Harbor Agent
│   └── dsh_agent.py           # DSH Adapter
│
├── harbor-lab/                # Harbor 本地测试任务
│   └── hellow-harbor/         # Hello Harbor Smoke Test
│
├── runs/                      # 实验运行结果（本地保存）
│
├── reports/                   # 实验报告与分析材料
│
├── scripts/                   # 实验辅助脚本
│
├── pyproject.toml             # Python 项目配置
├── uv.lock                    # 依赖锁定文件
└── README.md
```

## 6. 实验记录规范

每次实验应使用独立的 Job Name，避免覆盖已有结果。

Harbor 自动保存的实验记录包括：

- 任务配置与运行参数
- Agent 执行轨迹
- 工具调用及返回结果
- Verifier 测试结果
- Reward 与任务完成情况

原始运行记录保存在 `runs/harbor-jobs/`，整理后的实验数据和分析材料保存在 `reports/`。

实验结果必须来自真实运行记录，不得编造或修改实验数据。

## 7. Git 管理

建议提交：

- Agent 源码
- Benchmark 任务定义与测试脚本
- 实验配置
- 依赖锁定文件
- 整理后的实验报告

不提交：

- Python 虚拟环境
- API 密钥及 `.env` 文件
- 大量自动生成的原始运行日志
- 临时文件与缓存

---

**Project Status:** DSH 与 Harbor 已完成初步集成，Hello Harbor Smoke Test 已通过，正在完善 Adapter 并准备开展正式 Benchmark 实验。
