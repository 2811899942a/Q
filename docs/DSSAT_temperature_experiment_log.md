# DSSAT 温度改进连续实验日志

更新时间：2026-09-05
分支：`research/dssat-kt-sensitivity`
固定基线：DSSAT 4.8.5.0 / CERES-Maize / UFGA8201 / 6 treatments

## 记录规则

后续每轮实验必须记录以下内容：

1. 研究问题与实验目的；
2. 官方源码基线、数据版本与作物模型；
3. 修改文件、插入位置、公式与参数范围；
4. A/B 或零参数闭合检查；
5. GitHub Actions workflow run ID；
6. 编译、运行、解析过程中出现的错误与修复；
7. HWAM、ADAT、MDAT 等核心定量结果；
8. 机制解释与适用边界；
9. 当前阶段是否继续、降级或淘汰该路线；
10. 下一轮唯一优先任务。

所有阶段结果同时保存 CSV/Markdown，禁止只保留聊天结论。

---

## E01：PRFT 路径 KT 连续参数筛选

日期：2026-09-05
Workflow run：`33941472202`
状态：PASS

### 目的

检验新增连续温度响应强度参数 `KT` 是否能在严格可复现的 DSSAT 基准中产生可辨识作物响应。

### 基线

- 官方源码：`DSSAT/dssat-csm-os` tag `v4.8.5.0`
- 官方数据：`DSSAT/dssat-csm-data` tag `v4.8.5.0`
- 模型：CERES-Maize
- 试验：`UFGA8201.MZX`
- 处理数：6
- 评价变量：HWAM、ADAT、MDAT

### 源码改动与公式

官方 CERES-Maize 的光合作用温度因子 PRFT 保持原计算后，引入：

`PRFT_new = PRFT_original^(1 + KT)`

筛选范围：

`KT = -0.75, -0.50, -0.25, 0.00, +0.25, +0.50, +0.75, +1.00`

`KT=0` 必须严格回到官方输出。

### 实验过程中的实际问题

1. 第一次 GitHub Actions 中 DSSAT 编译成功，但运行时默认查找 `/DSSAT48/DSSATPRO.L48`，导致没有进入完整作物模拟。
2. 初版 shell 使用 `python ... | tee ...`，Python 失败退出码被管道掩盖，workflow 出现假绿灯。修复为 `set -euo pipefail`。
3. 随后暴露 `UFGA8201.WTH` 路径问题。定位到官方 `DSSATPRO.L48.in` 的 Weather、Soil、Genotype 路径由 `CMAKE_INSTALL_PREFIX` 生成，最终将编译/运行前缀统一锁定到 `/DSSAT48`。
4. 官方 `Summary.OUT` 的 `TNAM` 含空格，例如 `RAINFED LOW NITROGEN`，旧解析器只识别第 1 个处理。修复为按 DSSAT 表头并合并 TNAM 字段，6 个处理全部成功解析。
5. 修复后重新执行完整官方基线、KT=0 闭合和 KT 网格扫描。

### 数值结果

官方基线：

- HWAM RMSE = 970.523 kg/ha
- Willmott d = 0.979845
- ADAT MAE = 1.0 d
- MDAT MAE = 0.0 d

最佳筛选：

- `KT=+0.50/+0.75`
- HWAM RMSE = 970.202 kg/ha
- 相对官方仅改善 0.033%
- ADAT、MDAT 无变化

逐处理产量在最佳 KT 下仅有极小变化：

- T4：11854 -> 11853 kg/ha
- T6：10293 -> 10291 kg/ha
- 其余处理不变

官方基线到 `KT=0` 的 HWAM/ADAT/MDAT 数值闭合：PASS。

### 阶段判断

PRFT 单通道 KT 在当前基准中的杠杆过弱，难以承担核心创新。连续区域参数概念保留，参数作用位置转向 DTT/热量推进过程，并引入高温、低温和积温暴露信息。

### 归档

- `results/DSSAT_KT_phase1_results.md`
- `results/DSSAT_KT_phase1_screen.csv`
- `scripts/run_dssat_kt_screen.py`
- `.github/workflows/dssat-kt-sensitivity.yml`

---

## E02：TMAX、TMIN、DTT 三通道敏感性筛选

日期：2026-09-05
Workflow run：`33941735746`
状态：PASS

### 目的

在确定最终区域温度参数结构前，拆分三条温度作用通道：

1. 高温：只提高逐日 TMAX；
2. 低温：只降低逐日 TMIN；
3. 积温：官方 DTT 完成计算后、进入 SUMDTT/CUMDTT 累积前，对 DTT 施加比例扰动。

Phase 2 使用重新拉取的官方 4.8.5.0 源码和数据，避免继承 Phase 1 的 KT 修改。

### 零扰动闭合

`DTT x1.00` 对官方 HWAM、ADAT、MDAT：PASS。

官方基线平均 HWAM = 7109.67 kg/ha。

### 高温 TMAX 结果

- TMAX +1 C：平均 HWAM -472.67 kg/ha；ADAT MAE 3 d；MDAT MAE 4 d
- TMAX +2 C：平均 HWAM -786.50 kg/ha；ADAT MAE 3 d；MDAT MAE 5 d
- TMAX +3 C：平均 HWAM -1597.67 kg/ha；ADAT MAE 5 d；MDAT MAE 7 d
- TMAX +4 C：平均 HWAM -2515.67 kg/ha；ADAT MAE 6 d；MDAT MAE 9 d

结论：高温具有强烈且明显非线性的负产量响应，同时加快物候推进。

### 低温 TMIN 结果

- TMIN -1 C：平均 HWAM +569.50 kg/ha；ADAT MAE 6 d；MDAT MAE 5 d
- TMIN -2 C：平均 HWAM +1149.33 kg/ha；ADAT MAE 8 d；MDAT MAE 8 d
- TMIN -3 C：平均 HWAM +983.17 kg/ha；ADAT MAE 10 d；MDAT MAE 11 d
- TMIN -4 C：平均 HWAM +1705.00 kg/ha；ADAT MAE 12 d；MDAT MAE 15 d

结论：降低 Tmin 后的产量增加伴随严重物候延迟和观测误差恶化，当前响应中包含显著的积温减少—生育期延长效应，后续必须继续拆解低温直接胁迫与热量累积效应。

### DTT 结果

- DTT x0.85：平均 HWAM +1666.00 kg/ha；ADAT MAE 12 d；MDAT MAE 18 d
- DTT x0.90：平均 HWAM +897.33 kg/ha；ADAT MAE 10 d；MDAT MAE 12 d
- DTT x0.95：平均 HWAM +553.17 kg/ha；ADAT MAE 6 d；MDAT MAE 6 d
- DTT x1.00：闭合官方基线
- DTT x1.05：平均 HWAM -521.33 kg/ha；ADAT MAE 3 d；MDAT MAE 5 d
- DTT x1.10：平均 HWAM -1494.33 kg/ha；ADAT MAE 5 d；MDAT MAE 9 d
- DTT x1.15：平均 HWAM -1923.50 kg/ha；ADAT MAE 7 d；MDAT MAE 12 d

结论：DTT 为高杠杆温度通道。仅 ±5% 已使平均产量变化约 0.52–0.55 t/ha，并使吐丝/成熟移动数天。

### 当前参数结构候选

`DTT_adj = DTT_original * [1 + K_RT * E_T(stage)]`

`E_T(stage) = wH(stage)*EH + wL(stage)*EL + wG(stage)*EG`

其中：

- `K_RT`：区域温度适应/敏感系数；
- `EH`：高温暴露；
- `EL`：低温暴露；
- `EG`：积温偏差；
- `wH/wL/wG`：生育阶段权重。

该公式当前属于待验证候选结构，禁止在阶段敏感性和乌鲁木齐实测率定前写成最终模型公式。

### 适用边界

UFGA8201 当前承担可重复机制基准和代码验证功能。其筛选得到的数值不得直接作为乌鲁木齐参数。区域创新最终必须使用新疆/乌鲁木齐真实天气、玉米物候和产量观测进行率定与外部验证。

### 下一轮唯一优先任务

开展生育阶段敏感性试验：分别在营养生长期、抽雄—吐丝期、灌浆期、成熟前阶段扰动 TMAX/TMIN/DTT，得到阶段敏感度 `S_H(stage)`、`S_L(stage)`、`S_G(stage)`，据此确定权重和最终 K_RT 数学结构。

### 归档

- `results/DSSAT_temperature_component_phase2_results.md`
- `results/DSSAT_temperature_component_phase2_screen.csv`
- `scripts/run_dssat_temperature_component_screen.py`
- `.github/workflows/dssat-kt-sensitivity.yml`
