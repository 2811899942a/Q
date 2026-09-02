# 数据来源与公平比较规则

## 1. South Branch 数据分层

所有已有参数—模拟结果必须按生成机制分层保存：

### A. Broad, observation-independent library

来自 Sobol/LHS/均匀先验等与 USGS 目标函数无关的广域参数采样。该层允许用于：

- 确定性 inverse model 训练；
- NPE posterior 训练；
- synthetic held-out diagnostics；
- 训练规模曲线 250/500/1000/2500/5000。

### B. Observation-directed optimization traces

来自 DeepCal、DDS、DE、BO、TuRBO 等已经读取真实 USGS 目标的定向轨迹。该层包含目标信息，主公平实验中不得并入离线训练库。

它只允许用于：

- 失败诊断；
- 次级“历史资产复用”情景；
- 算法轨迹审计；
- 作为已发生在线成本完整计入总账。

将 B 层混入主 NPE 训练会形成 observed-target information advantage，破坏与 DDS/TuRBO 的 from-scratch 公平比较。

## 2. 三种成本口径

```text
N_offline = 生成 observation-independent 训练库的 Real-SWAT+ 次数
N_online  = 给定真实 Qobs 后新增的 Real-SWAT+ 次数
N_total   = N_offline + N_online
```

必须同时报告：

1. **Online/amortized efficiency**：已有训练库条件下的新增成本；
2. **From-scratch total efficiency**：从零开始的全部 Real-SWAT+ 成本；
3. **Asset-reuse scenario**：利用现有5000套数据时的工程收益，单独列示。

在单流域、单目标条件下，5000套训练库无法被视为免费。总成本优势必须通过小训练库或多任务复用实证。

## 3. 公开 DL4SWAT 数据

公开复现数据与 South Branch 数据物理隔离，保存独立 manifest、hash、训练划分和输出目录。公开数据只用于复现前人方法，不向 South Branch 模型提供迁移权重，除非未来另立经预注册的迁移学习实验。

## 4. 时间封锁

- 2000–2002：warm-up/context；
- 2003–2016：development；
- 2017–2020：locked validation；
- 2021–2024：final test。

方法、输入表示、参数范围、后验结构、OOD规则和优化预算均在 development 内冻结。
