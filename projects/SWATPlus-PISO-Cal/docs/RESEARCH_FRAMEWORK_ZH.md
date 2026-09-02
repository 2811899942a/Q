# SWAT+ 快速高精度率定研究框架（冻结版）

## 1. 研究目标

唯一主目标：利用深度学习提供参数候选先验，再由真实观测目标驱动的序贯搜索完成纠偏，以更少的 Real-SWAT+ 调用达到不低于 DDS/TuRBO 的多站率定精度。

## 2. 方法名称与职责分工

工作名：PISO-Cal（Posterior-Informed Sequential Optimization for SWAT+ Calibration）。

三个部件各司其职：

1. 时序编码器从多站径流中提取参数相关信息；
2. Neural Posterior Estimation 输出多个可能成立的参数区域；
3. 真实 USGS 目标驱动的局部序贯优化决定最终参数。

概率反演结果只承担候选生成和冷启动。Real-SWAT+ 与真实多站目标始终拥有最终裁决权。

## 3. 必须修正的标准 SNPE 误用

标准 SNPE 的新训练样本仍是 `(theta, simulator_output)`。真实观测没有对应的真实参数标签，不能把 `(theta, Qobs)` 或 observed NSE 伪装成 SNPE 监督样本。

本项目采用：

```text
simulation-trained posterior
        ↓
OOD/misspecification check
        ↓
posterior-prior mixture candidates
        ↓
fresh Real-SWAT+
        ↓
observed multi-gauge objective
        ↓
online objective surrogate / trust region
```

因此，posterior 更新和真实目标纠偏在统计上保持清晰分工。

## 4. 研究阶段

### R0 公开论文复现

复现 Mudunuru et al. 的 DL4SWAT 数据与确定性 CNN 反演。使用公开 1000 套 SWAT 模拟、观测径流与既有划分。由于原 GitHub 仓库没有明确软件许可证，采用 clean-room 重写，公开数据按 CC BY 4.0 引用。

### R1 South Branch 确定性编码器比较

同一数据、同一划分、同一参数损失下比较 CNN、TCN、BiLSTM、小型 Transformer。模型比较只负责选择输入编码器，不能作为主要创新。

评价分两层：

- synthetic held-out 参数 NRMSE/MAE；
- 预测参数写回 Real-SWAT+ 后的真实多站 NSE、KGE、PBIAS 和最弱站 NSE。

### R2 概率参数反演

对 Top-2 编码器训练 NPE，默认以 MAF 为第一版密度估计器。输出 `p(theta | Qsim)`，保留 equifinality 和参数相关结构。

必须完成 SBC、coverage、TARP 和 posterior predictive checks。

### R3 真实观测域偏移审计

将 Qobs 的编码表示与训练模拟分布比较，计算 kNN 距离百分位。根据 OOD 程度，将 posterior 与参数 prior 混合：

- OOD <= 95%：posterior 权重 0.8；
- 95%-99%：posterior 权重 0.5；
- >99%：posterior 权重 0.2。

该阈值在正式 pilot 前冻结，并做 0.2/0.5/0.8 敏感性附录。

### R4 Posterior-informed fresh pilot

每个方法和 seed 共 198 次 Real-SWAT+：42 个共同 Sobol 初始点，随后 26 轮、每轮 6 个候选。

比较：

- DDS；
- TuRBO；
- PISO-Cal。

PISO 每轮候选：4 个来自真实目标 surrogate acquisition，1 个来自 posterior-guided candidate，1 个用于不确定性/多样性。posterior 候选若不满足主目标竞争性门槛，自动退化为标准 surrogate 候选。

### R5 正式确认

Pilot 通过后，使用五个 paired seeds 和 300 次预算。模型冻结后再打开 2017-2020 locked validation，随后一次性评价 2021-2024 final test。

## 5. 创新边界

已有工作已经分别验证 CNN 反演 SWAT 参数、SBI posterior、SNPE、normalizing flow 和 multi-gauge calibration。

本项目的潜在增量集中在：

1. SWAT+ 真实三站条件下的概率逆率定；
2. 明确诊断 simulator-observation misspecification；
3. 根据 OOD 自适应调节 posterior 信任度；
4. 将 posterior 作为冷启动先验，与真实目标序贯优化形成可核算的闭环；
5. 同时报告离线、在线和总 Real-SWAT+ 成本。

## 6. 结果预期等级

在当前 14D 证据下，正式目标分级：

- 基线目标：稳定达到 mean NSE 0.557；
- 有价值目标：0.58-0.60，且显著减少评价次数；
- 强结果：0.60-0.62，三站均无明显退化；
- 0.65：扩展目标；
- 0.70：当前证据不足，不作为项目承诺。

## 7. 成本口径

必须同时报告：

```text
N_offline = 训练 inverse/posterior 使用的 SWAT 模拟数
N_online  = 面对 Qobs 后新增的 Real-SWAT+ 数
N_total   = N_offline + N_online
```

在线快和总成本快分开表述。已有 5000 套数据可以作为资产情景，同时还要做 250/500/1000/2500/5000 的训练规模曲线。
