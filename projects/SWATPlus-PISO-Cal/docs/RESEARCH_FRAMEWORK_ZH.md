# SWAT+ 快速高精度率定研究框架（A流域冻结版）

## 1. 研究区锁定

正式研究区始终是此前一直使用的 **A流域 South Branch Potomac**。

现有工程继续使用：

- SWAT+ rev.62.0.0；
- USGS 01605500（ch12）；
- USGS 01606000（ch17）；
- USGS 01606500（ch18）；
- 14维既有率定参数空间；
- 2000–2002 warm-up/context；
- 2003–2016 development；
- 2017–2020 locked validation；
- 2021–2024 final test。

任何已发表论文中的流域、SWAT工程或观测数据都不替换该研究区。论文只提供方法框架、复现锚点和对照基线。

## 2. 唯一主目标

利用深度学习为 A 流域 SWAT+ 提供高价值参数候选/参数后验，再由真实三站 USGS 目标驱动的 Real-SWAT+ 序贯搜索完成最终率定，以更少的 Real-SWAT+ 调用达到不低于 DDS/TuRBO 的率定精度。

工作名：PISO-Cal（Posterior-Informed Sequential Optimization for SWAT+ Calibration）。

## 3. 前人论文的角色

### DL4SWAT

Mudunuru et al. 的工作只作为方法母体：

```text
SWAT simulations
→ streamflow encoder
→ inverse parameter model
→ SWAT parameter candidates
```

公开数据可用于 clean-room 复现，以确认 inverse-calibration 实现逻辑正确，但该公开流域不进入正式 A 流域实验。

### Hydrologic SBI

Hull et al. 等工作提供：

```text
single point estimate
→ parameter posterior p(theta|Q)
→ sequential simulation-based inference
→ misspecification awareness
```

本项目将这些成熟思想迁移并改造到 A 流域真实三站 SWAT+ 率定。

## 4. 方法结构

三个部件各司其职：

1. 时序编码器从 A 流域三站 SWAT+ 模拟径流中提取参数相关信息；
2. Neural Posterior Estimation 输出多个可能成立的14维参数区域；
3. 真实 USGS 目标驱动的局部序贯优化决定最终参数。

概率反演结果只承担候选生成和冷启动。Real-SWAT+ 与真实三站目标始终拥有最终裁决权。

标准 SNPE 的训练样本始终是 `(theta, Qsim)`。真实观测没有对应的真实 SWAT 参数标签，不能把 `(theta, Qobs)` 或 observed NSE 伪装成 SNPE 监督样本。

正式流程：

```text
A流域 observation-independent broad simulations
        ↓
(theta, Qsim_3gauges)
        ↓
CNN/TCN/BiLSTM/Transformer encoder screen
        ↓
NPE posterior p(theta | Qsim)
        ↓ condition on real A-basin Qobs
OOD / simulator-observation support diagnostic
        ↓
posterior/prior proposal mixture
        ↓
fresh A-basin Real-SWAT+
        ↓
real three-gauge objective
        ↓
TuRBO/local sequential optimization
        ↓
final calibrated theta*
```

## 5. 正式研究阶段

### A0 A流域接管与数据审计

首先处理现有 South Branch 工程，不重建其他流域。

必须核验：

- 正式 SWAT+ rev.62 工程路径；
- 三站通道映射；
- 14D 参数名称、上下界、写入语义；
- 2003–2016 三站 observed objective；
- 当前正式 Real-SWAT+ runner；
- 已有 simulation archive 的数据来源。

已有模拟必须拆成两层：

1. observation-independent broad simulations：Sobol/LHS/均匀等未读取 USGS objective 的广域采样；
2. observed-directed traces：DeepCal/DDS/DE/BO 等已经根据真实 USGS 目标生成的轨迹。

主 inverse/NPE 训练只允许使用第1层。

A0 必须完成一个正式候选参数的 old-runner/new-runner 逐日输出和指标等价审计。

### A1 DL4SWAT-style 确定性 inverse baseline

在 A 流域 broad simulations 上直接建立：

```text
Qsim_3gauges → theta_14D
```

比较：

- 1D-CNN；
- TCN；
- BiLSTM；
- 小型/patch Transformer。

所有模型使用相同 realization split、train-only scaler、损失函数和 seed。

评价分两层：

- synthetic held-out 参数 NRMSE/MAE；
- 预测参数重新写入 A 流域 Real-SWAT+ 后的真实三站 Mean NSE、Worst-gauge NSE、KGE、PBIAS。

模型比较只是工程筛选，不作为主要创新。

可选的公开 DL4SWAT clean-room reproduction 可在 A0/A1 前后单独进行，仅用于验证 implementation sanity，不作为研究主流程 Gate 的替代品。

### A2 概率参数反演

保留 A1 前两名 encoder。

训练 NPE：

```text
p(theta_14D | Qsim_3gauges)
```

首选 MAF/NSF。

必须完成：

- simulation-based calibration；
- 50/80/95% empirical coverage；
- TARP；
- posterior predictive checks；
- 参数边界坍缩与参数相关结构检查。

synthetic posterior 不通过则停止，不进入真实观测。

### A3 真实观测域偏移审计

比较真实三站 USGS 序列与 A 流域 simulation-training distribution。

采用 embedding-space support/OOD diagnostic。posterior 信任权重需要通过受控 misspecification 实验冻结，不允许根据最终真实率定结果反调。

失配实验包括：

1. held-out A流域 SWAT+ simulation；
2. forcing perturbation；
3. additive/multiplicative observation noise；
4. structural proxy mismatch；
5. real USGS observation。

### A4 Fresh Real-SWAT+ 决定性 pilot

正式比较：

- DDS；
- TuRBO；
- Point-Warm-TuRBO；
- Posterior-Only；
- PISO-Cal。

决定性主比较：

```text
PISO-Cal vs TuRBO
```

基础预算：每方法/seed 42 个共同 Sobol 初始点 + 156 adaptive = 198 fresh Real-SWAT+ evaluations；3 paired seeds。

跟踪：

```text
Best Mean NSE @60/@100/@150/@198
N0.557
N0.58
N0.60
Worst-gauge NSE
KGE
PBIAS
wall-clock
failure rate
```

### A5 正式确认

A4 通过后才进行：

- 5 paired seeds；
- 300 evaluations/method/seed；
- 必要消融；
- 方法完全冻结；
- 打开2017–2020 locked validation一次；
- 最后打开2021–2024 final test一次。

## 6. 创新边界

本项目不宣称 CNN、TCN、Transformer、NPE、normalizing flow、TuRBO 或 multi-gauge calibration 本身新颖。

潜在方法增量集中在：

1. A流域 SWAT+ 真实三站条件下的概率逆率定；
2. simulation-trained posterior 在真实观测中的 support/misspecification 诊断；
3. 根据失配程度控制 posterior 作为候选先验的可信度；
4. posterior cold-start 与 fresh Real-SWAT+ observed-objective sequential optimization 的结合；
5. 离线、在线和总 Real-SWAT+ 成本统一核算。

只有 PISO-Cal 在严格配对 fresh pilot 中超过 TuRBO，才允许把 posterior-informed mechanism 作为核心创新。

## 7. 结果目标

现阶段14D目标：

- 基线：稳定达到 Mean NSE 0.557；
- 有价值：0.58–0.60，并明显减少 Real-SWAT+ evaluations；
- 强结果：0.60–0.62，三站均无明显退化；
- 0.65：扩展目标；
- 0.70：当前不作为承诺。

“快”与“准”分别定义：

```text
快 = 达到同一 NSE 门槛所需 fresh Real-SWAT+ evaluations 更少
准 = 相同 Real-SWAT+ 预算下 Mean NSE/KGE 更高且 Worst-gauge 不明显恶化
```

Pilot通过条件：

1. 达到同一目标至少减少25% fresh Real-SWAT+ evaluations；或
2. 相同预算下 median Mean NSE 至少提高0.02，Worst-gauge NSE损失不超过0.03；
3. 优势必须在3个 paired seeds 的中位结果上存在。

## 8. 成本口径

必须分别报告：

```text
N_offline = 生成/训练 inverse posterior 使用的 observation-independent SWAT+ simulations
N_online  = 面对真实 USGS 后新增的 fresh Real-SWAT+ evaluations
N_total   = N_offline + N_online
```

已有5000套 broad simulations属于历史资产情景，不能在 from-scratch 论文结论中当作免费数据。

同时做 250/500/1000/2500/5000 训练规模曲线。

## 9. 主结论层级

- PISO-Cal > TuRBO > DDS：posterior-informed sequential optimization 成立；
- PISO-Cal ≈ TuRBO > DDS：局部代理优化有效，posterior增量不足；
- DDS ≥ TuRBO/PISO-Cal：停止该方法线；
- 无论哪种结果，正式研究区始终保持 A流域 South Branch Potomac，不更换研究区。
