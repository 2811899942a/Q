# 下一对话执行交接

## 固定研究区与研究目标

正式研究区始终是 **A流域 South Branch Potomac**，使用现有 SWAT+ rev.62 三站工程：

- USGS 01605500（ch12）
- USGS 01606000（ch17）
- USGS 01606500（ch18）

时间边界继续锁定：

- 2000–2002：warm-up/context
- 2003–2016：development
- 2017–2020：locked validation
- 2021–2024：final test

研究目标：参考已发表 DL4SWAT / SBI 等方法框架，在 **现有 A 流域** 上开发并验证“深度学习辅助的又快又准 SWAT+ 率定”。论文原流域只用于方法复现/代码正确性参照，绝不替换 A 流域，也不把论文流域数据混入 A 流域正式训练。

## 固定身份

下一对话负责本项目的 Codex 指令、代码审查、运行结果核验和 Gate 判定。不得重新扩大到 V3B、跨流域、CMIP6、PLUS 或新的强耦合架构。

## 仓库位置

```text
2811899942a/Q/projects/SWATPlus-PISO-Cal
```

## 第一优先任务：A流域接管审计

先处理现有 South Branch A 流域，不重建其他研究区：

1. 定位并读取现有 A 流域正式 SWAT+ rev.62 工程；
2. 核对三站/通道映射、2003–2016 development objective、14D 参数定义和边界；
3. 核对当前正式 Real-SWAT+ runner、参数写入、输出解析和指标计算；
4. 将已有 5000 broad simulations 与 DeepCal/DDS/DE/BO 等 observed-directed traces 彻底分层；
5. 将 observation-independent broad simulations 转为统一 data contract：`theta[N,14]`、`qsim[N,3,T]`、`qobs[3,T]`；
6. 使用一个正式候选参数对旧 runner 与新项目 runner 做逐日等价审计；
7. 只有以上全部 PASS，才进入深度学习反演。

## 论文方法复现的角色

DL4SWAT 公开数据/代码只承担 implementation sanity check：

- 可选地下载 Zenodo 10.5281/zenodo.7271945；
- clean-room 重现论文 CNN inverse calibration 的基本行为；
- 用来确认数据预处理、inverse-model 训练、参数输出逻辑没有实现错误。

禁止：

- 重建 DL4SWAT 论文流域作为正式研究区；
- 把论文流域的模型权重/流量/参数样本直接迁入 A 流域正式结果；
- 因论文复现耗时而阻塞 A 流域数据链审计。

## A流域正式方法顺序

### A0 数据与执行器审计

必须 PASS：

- 14D 参数与边界；
- 三站 development 观测；
- broad/observed-directed provenance；
- old/new runner equivalence；
- evaluation accounting。

### A1 确定性 inverse baseline

在 A 流域 broad simulations 上比较：

- 1D-CNN（DL4SWAT-style baseline）；
- TCN；
- BiLSTM；
- small/patch Transformer。

所有模型同一数据、同一 realization split、train-only scaler、同一参数损失。预测参数必须重新写回 A 流域 Real-SWAT+，以真实三站 objective 验证。

### A2 概率反演

Top-2 encoder + NPE（MAF/NSF），训练目标仅为 `(theta, Qsim)`。

完成 SBC、coverage、TARP、PPC 后才能进入真实观测。

### A3 simulator-observation misspecification

对真实三站 USGS 观测计算 OOD/support diagnostic，冻结 posterior trust 规则。

### A4 fresh Real-SWAT+ pilot

正式比较：

```text
DDS
TuRBO
Point-Warm-TuRBO
Posterior-Only
PISO-Cal
```

决定性比较：PISO-Cal vs TuRBO。

基础 pilot 预算：每方法/seed 42 个共同初始点 + 156 adaptive = 198 fresh Real-SWAT+ evaluations，3 paired seeds。

## 禁止事项

- 不更换研究区；
- 不扩参数维度；
- 不提前读取 2017–2020 / 2021–2024；
- 不把 observed-directed 历史轨迹混进 from-scratch NPE 训练；
- 不把5000套 broad simulations 当成零成本；
- 不用 archive replay 替代 fresh Real-SWAT+；
- 不以单 seed 宣称胜出；
- 不继续扩展模型动物园；
- 不把 posterior 自身当最终率定结果；最终参数必须由 A 流域 Real-SWAT+ + USGS objective 验证。

## 下一对话第一份 Codex 指令

```text
TASK = A0_SOUTH_BRANCH_PISO_TAKEOVER_AUDIT

STUDY_AREA = South Branch Potomac A basin
SWATPLUS = existing rev.62 project
GAUGES = 01605500/ch12, 01606000/ch17, 01606500/ch18
PARAM_DIM = 14
DEVELOPMENT = 2003-2016
LOCKED_VALIDATION = 2017-2020
FINAL_TEST = 2021-2024

GOALS:
1. locate formal A-basin project and current runner;
2. freeze the exact 14D parameter dictionary/bounds/write semantics;
3. verify observed three-gauge development series and objective;
4. classify all simulation archive rows as observation-independent broad or observed-directed;
5. build theta/qsim/qobs data contract from A-basin broad simulations;
6. execute one-candidate old/new runner equivalence audit;
7. output data hashes and evaluation accounting.

OUTPUT:
- A0_project_manifest.json
- A0_parameter_dictionary.csv
- A0_archive_provenance.csv
- A0_data_contract_manifest.json
- A0_runner_equivalence_report.md
- A0_gate_report.md

STOP:
- do not train CNN yet;
- do not use paper watershed as study area;
- do not run SBI;
- do not open locked validation/final test;
- do not generate large new Real-SWAT batches.
```

## Gate reporting template

```text
STAGE=
STATUS=PASS|FAIL|BLOCKED
STUDY_AREA_LOCK=A_SOUTH_BRANCH_POTOMAC
PARAMETER_SPACE_OK=
DATA_PROVENANCE_OK=
RUNNER_EQUIVALENCE=
LEAKAGE_AUDIT=
PRIMARY_FINDINGS=
NEXT_ALLOWED_ACTION=
```
