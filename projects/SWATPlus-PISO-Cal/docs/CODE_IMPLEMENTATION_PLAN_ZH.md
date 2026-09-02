# 代码实现计划——A流域优先版

## 1. 正式入口

第一任务永远是 `A0_SOUTH_BRANCH_PISO_TAKEOVER_AUDIT`。Public DL4SWAT reproduction 为可选 P0，不再是进入 A 流域研究的前置门。

新增硬锁模块：

```text
src/swatplus_piso/study_area.py
src/swatplus_piso/swat/south_branch.py
```

正式 A 流域数据必须通过 `load_south_branch_dataset()`，自动拒绝错误流域、错误站点、非14D、目标导向训练轨迹以及 locked period 泄漏。

## 2. A0：接管现有 South Branch 工程

Codex 扫描：

```text
D:/SWAT+_3V3/A_SouthBranchPotomac/
```

定位当前正式版本，而不是默认某个旧子目录。

必须提取并冻结：

1. SWAT+ executable 与 revision；
2. 正式 TxtInOut/Scenarios/运行目录；
3. 14D 参数名称、上下界、写入模式、目标文件/字段；
4. ch12/ch17/ch18 与 USGS 三站映射；
5. development Qobs；
6. 当前 formal objective 的源代码/公式/权重；
7. 当前正式 parameter writer/output parser；
8. 所有 simulation archive 的生成机制。

生成 sha256 manifest。PISO 不重写物理模型、不重新定义 objective。

## 3. archive分层

### A层：observation-independent broad

允许作为 inverse/NPE 正式训练库。每行必须能追溯 `theta -> Real-SWAT+ -> qsim`。

### B层：observed-directed

DeepCal/DDS/DE/BO/TuRBO 等读取过真实 objective 的轨迹。主训练库禁止使用。保留用于历史诊断和 asset-reuse 附加实验。

## 4. runner接入

使用 `SouthBranchLegacyAdapter` 包裹现有 writer/parser：

```python
adapter = SouthBranchLegacyAdapter(existing_writer, existing_parser)
runner = adapter.build_runner(template_dir, executable_name, scratch_root)
```

禁止重新写一套不同参数语义的 writer。

同一个正式 theta 必须同时通过：

```text
旧正式runner
新RealSWATRunner+SouthBranchLegacyAdapter
```

要求三站逐日输出完全一致；若底层文件格式引入可解释的浮点序列化差异，必须先记录证据再显式放宽 `atol`。

## 5. A1：DL4SWAT-style A流域确定性反演

先做 1D-CNN 基线，再做 TCN/BiLSTM/Patch Transformer。同一 realization split、train-only scaler、同一14D参数损失、同seed。

评估两层：

1. synthetic held-out 参数 MAE/NRMSE；
2. 对真实三站 Qobs 反演 theta 后，必须 fresh Real-SWAT+ 重跑并计算正式 inherited objective。

模型排名只是 encoder screen，不作为主创新。

## 6. A2：概率反演

Top-2 encoder + `sbi==0.27.0` NPE，优先 MAF/NSF。

训练样本只能是 `(theta, Qsim)`。必须做 SBC、coverage、TARP、PPC。

## 7. A3：simulation-observation gap

使用受控失配实验确定并冻结 posterior trust 规则。不得根据 A4 正式结果反向调 OOD 阈值。

## 8. A4：fresh Real-SWAT+ pilot

所有方法共用同一：

- 14D bounds；
- inherited objective；
- 42 common initial points；
- paired seeds；
- evaluation accountant；
- W6 runner；
- checkpoint/retry/dedup。

正式比较 DDS、TuRBO、Point-Warm-TuRBO、Posterior-Only、PISO-Cal。决定性因果比较为 PISO-Cal vs TuRBO。

## 9. 代码质量门

```text
A. compile/import PASS
B. pytest PASS
C. A-basin metadata hard-lock tests PASS
D. archive provenance manifest PASS
E. one-candidate old/new runner daily equivalence PASS
F. development objective equality PASS
G. W6 formal execution-context dry-run PASS
H. evaluation accounting PASS
```

C–H 未完成前，不启动 A4。
