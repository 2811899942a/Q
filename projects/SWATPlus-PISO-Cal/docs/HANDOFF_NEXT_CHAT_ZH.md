# SWATPlus-PISO-Cal 下一对话完整交接

## 0. 一句话任务

在**原来的 A 流域 South Branch Potomac**上，参考已发表 DL4SWAT 的深度学习参数反演框架，并引入概率后验与真实观测序贯纠偏，研究能否用更少的 Real-SWAT+ 运行获得与 DDS/TuRBO 相同或更高的三站率定精度。

任何情况下都不更换研究区。

---

## 1. 正式研究区硬锁

- Study area ID：`A_SOUTH_BRANCH_POTOMAC`
- 模型：现有 **SWAT+ rev.62** 工程
- 本地优先扫描根目录：`D:/SWAT+_3V3/A_SouthBranchPotomac/`
- 不假定某个历史子目录仍是最新正式版本；由 Codex 扫描后确定 canonical project。

三站固定：

| USGS | channel |
|---|---:|
| 01605500 | 12 |
| 01606000 | 17 |
| 01606500 | 18 |

时间固定：

- 2000–2002：warm-up/context
- 2003–2016：development
- 2017–2020：locked validation
- 2021–2024：final test

参数空间固定为现有正式14D。名称、上下界和写入语义必须从当前正式 A 流域 runner 提取，不可凭记忆重建。

正式 objective 同样从现有 A 流域 calibration workflow 继承，在 A0 形成快照和 hash 后冻结。PISO 项目不得重新设计目标函数来追求更好结果。

---

## 2. 论文框架到底怎么用

Mudunuru/DL4SWAT 是**方法母论文**，用途是：

```text
SWAT simulations: theta -> Qsim
             ↓
DL inverse mapping: Q -> theta
             ↓
real observed Qobs -> predicted theta
             ↓
write theta back to SWAT and verify
```

我们在 A 流域先复现这一思想，再升级：

```text
A-basin broad Real-SWAT+ library
        ↓
CNN/TCN/BiLSTM/Transformer inverse encoder
        ↓
point theta baseline
        ↓
NPE: p(theta | three-gauge Q)
        ↓
OOD/misspecification trust
        ↓
TuRBO + guarded posterior candidates
        ↓
fresh A-basin Real-SWAT+ + real USGS objective
```

论文原流域只可做可选 public-data implementation sanity check。它不是正式研究区，不重建，不混数据，不默认迁移权重。

---

## 3. 为什么放弃上一条路线

后续对话不要重新救旧 DeepCal controller/dynamic-subspace 方案。

历史实验证据：

- SWAT-to-SWAT pseudo-target DeepCal 约0.92；
- 真实 USGS DeepCal 约0.506；
- 同14D、约200 Real-SWAT evaluations 的 DDS 约0.557；
- Diagnosis contribution 接近0；Dynamic Subspace、Process Repair、Rescue 消融为负或无益；
- archive replay 被历史 optimizer trajectory 富集，Random 高分不能作为算法结论。

当前新思路针对两个核心问题：

1. equifinality：不再强迫 `Q -> 唯一theta`，而学习 `p(theta|Q)`；
2. simulator-observation gap：后验只做候选先验，最终由 fresh Real-SWAT+ + real objective 在线纠偏。

---

## 4. archive必须严格分层

历史 archive 约7400行：

### A层：observation-independent broad，约5000

与真实 USGS objective 无关的 broad sampling。主 A1/A2 训练只允许使用这一层。

历史 broad pool 最大 mean NSE 约0.496。这个事实说明真实优质区可能位于 broad library 稀疏区，因此 PISO 必须保留 TuRBO/prior escape 能力，不能让 posterior 垄断搜索。

### B层：observed-directed，约2400

DeepCal/DDS/DE/BO 等已经读取 Qobs objective 的轨迹。这些点含目标信息，禁止并入 from-scratch inverse/NPE 主训练库。

它们只可用于失败分析或单独 asset-reuse 情景，并完整核算其生成成本。

A0必须按真实文件重新统计行数、来源和 hash；上述数字只是定位线索。

---

## 5. 代码仓库

GitHub：

`2811899942a/Q/projects/SWATPlus-PISO-Cal`

优先阅读：

1. `docs/A_BASIN_LOCK.md`
2. `docs/HANDOFF_NEXT_CHAT_ZH.md`
3. `docs/RESEARCH_FRAMEWORK_ZH.md`
4. `docs/CODE_IMPLEMENTATION_PLAN_ZH.md`
5. `docs/DATA_CONTRACT.md`
6. `docs/DATA_PROVENANCE_AND_FAIRNESS_ZH.md`
7. `docs/DECISION_GATES.md`
8. `docs/EXPERIMENT_MATRIX.md`
9. `docs/PROJECT_STATE.md`
10. `configs/south_branch.yaml`

代码硬锁：

- `study_area.py`：A流域、三站、14D、时间硬锁；
- `load_south_branch_dataset()`：正式数据 fail-closed 验证；
- `SouthBranchLegacyAdapter`：要求复用旧正式 writer/parser；
- `assert_daily_equivalence()`：旧/新 runner 等价门。

---

## 6. 第一阶段 A0：只做接管审计

第一份 Codex 指令必须是：

```text
TASK = A0_SOUTH_BRANCH_PISO_TAKEOVER_AUDIT

ROOT_SCAN = D:\SWAT+_3V3\A_SouthBranchPotomac
STUDY_AREA_LOCK = A_SOUTH_BRANCH_POTOMAC
SWATPLUS_EXPECTED_REV = 62.0.0
GAUGE_ORDER = 01605500/ch12,01606000/ch17,01606500/ch18
PARAM_DIM = 14
DEVELOPMENT = 2003-01-01..2016-12-31
LOCKED_VALIDATION = 2017-2020
FINAL_TEST = 2021-2024

DO:
1. recursively inventory the A-basin root without modifying model files;
2. identify the current canonical formal SWAT+ project and executable;
3. locate the current production parameter writer, output parser, objective code and observations;
4. export exact 14D parameter dictionary: name, lower, upper, transform, change_type, target_file, target_field;
5. snapshot/hash the formal objective definition and three-gauge mapping;
6. inventory every simulation/archive table and classify each row/source as observation-independent broad or observed-directed;
7. rebuild ONLY the broad layer into theta[N,14], qsim[N,3,T], qobs[3,T], dates.csv, parameter_bounds.csv, metadata.json;
8. validate with `swatplus-piso validate-a-basin-data <root>`;
9. connect existing writer/parser through SouthBranchLegacyAdapter; do not rewrite parameter semantics;
10. choose one previously verified formal theta and run both old and new runners;
11. require three-gauge daily equivalence and identical inherited objective;
12. audit evaluation accounting and W6 worker equivalence.

OUTPUT:
- A0_project_inventory.txt
- A0_canonical_project.json
- A0_parameter_dictionary.csv
- A0_parameter_dictionary.sha256
- A0_objective_snapshot.txt
- A0_objective.sha256
- A0_archive_provenance.csv
- A0_archive_summary.json
- A0_data_contract/
- A0_runner_equivalence_report.md
- A0_evaluation_accounting_report.md
- A0_GATE_REPORT.md

DO NOT:
- do not build another watershed;
- do not use the paper watershed as formal data;
- do not train any neural network;
- do not run SBI;
- do not open 2017-2020 or 2021-2024;
- do not generate a large new Real-SWAT batch;
- do not merge optimizer-enriched traces into broad training data;
- do not alter the 14D bounds or objective.

GATE FORMAT:
STAGE=A0_SOUTH_BRANCH_PISO_TAKEOVER_AUDIT
STATUS=PASS|FAIL|BLOCKED
STUDY_AREA_LOCK=A_SOUTH_BRANCH_POTOMAC
CANONICAL_PROJECT=
SWAT_REVISION=
GAUGE_MAP_OK=
PARAMETER_SPACE_OK=
OBJECTIVE_HASH=
BROAD_ROWS=
OBSERVED_DIRECTED_ROWS=
DATA_CONTRACT_OK=
RUNNER_DAILY_EQUIVALENCE=
OBJECTIVE_EQUIVALENCE=
EVALUATION_ACCOUNTING=
LOCKED_PERIOD_LEAKAGE=NO|YES
NEXT_ALLOWED_ACTION=
```

A0 未 PASS，不进入 A1。

---

## 7. A1：在A流域复现论文方法思想

A1不是去复现论文流域。是在 A 流域 broad simulations 上复现 `Q -> theta` inverse calibration。

冻结四个 encoder：

```text
1D-CNN    # DL4SWAT-style主复现基线
TCN
BiLSTM
Patch Transformer
```

所有模型：同一数据、同一 split、同一 scaler、同一14D loss、同一 seeds。

每个模型最终都必须执行：

```text
real 2003-2016 three-gauge Qobs
        ↓
inverse model
        ↓
predicted theta14
        ↓
fresh Real-SWAT+
        ↓
inherited three-gauge objective
```

synthetic parameter RMSE好看不能替代 Real-SWAT+ 验证。

A1只选 Top-2 encoder，不继续扩模型动物园。

---

## 8. A2/A3/A4

### A2 posterior

Top-2 + NPE；MAF/NSF。训练只有 `(theta,Qsim)`。完成 SBC、coverage、TARP、PPC。

### A3 misspecification

用 synthetic mismatch 预先冻结 posterior trust。禁止根据 A4 结果调阈值。

### A4 fresh pilot

比较：

```text
DDS
TuRBO
Point-Warm-TuRBO
Posterior-Only
PISO-Cal
```

核心比较：PISO-Cal vs TuRBO。

每方法/seed：42 common initial + 156 adaptive = 198；3 paired seeds。

PASS：达到同一目标至少少25% fresh evaluations，或同预算 median mean NSE 至少+0.02，同时 worst gauge 损失不超过0.03。

---

## 9. 计算与worker口径

当前机器历史实测：

```text
W2=179.46 runs/hour
W4=346.37
W6=453.98
W8=419.59
```

W6为当前本机默认。若换服务器/工程目录/存储环境，必须重新做 W4/W6/W8/W12/W16 scaling benchmark。

正式批量前仍须执行同一正式 runner 的端到端 dry-run，不能仅靠 compile/selftest 判定部署成功。

---

## 10. 当前明确禁止恢复的分支

```text
V3B新计算                     DEFERRED
DeepCal frozen controller      TERMINATED
Diagnosis -> dynamic subspace  TERMINATED
Process Repair强干预           TERMINATED
archive replay正式benchmark     FORBIDDEN
参数维度扩展                   FORBIDDEN before A4
跨流域/CMIP6/PLUS              DEFERRED
强耦合结构                     OUT OF SCOPE
```

当前唯一主线：

**A流域 + 已发表 inverse calibration 母框架 + posterior + observed-objective sequential correction + fair Real-SWAT accounting。**
