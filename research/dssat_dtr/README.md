# DSSAT-DTR：新疆大昼夜温差条件下 DSSAT 温度过程改进

## 1. 研究问题

目标不是简单修正气象输入，而是评估并改进 DSSAT 在干旱大陆性、大昼夜温差环境下的亚日尺度温度重构与温度响应过程。

核心假设：

- H1：DSSAT 当前固定参数的 Parton–Logan 小时温度重构，在高 DTR 条件下存在可识别的系统误差。
- H2：基于新疆实测逐小时温度进行区域化或结构性改进，可以降低小时温度重构误差。
- H3：温度重构误差的降低会传递到热时间、物候、生物量和产量模拟，并改善 DSSAT-CERES-Maize 的区域适用性。

---

## 2. 科学证据矩阵

| 层级 | 关键问题 | 理论/文献依据 | 对本研究的作用 | 当前判断 |
|---|---|---|---|---|
| A | 如何从日 Tmax/Tmin 构造日内温度 | Parton & Logan (1981), *A model for diurnal variation in soil and air temperature* | DSSAT 当前 HTEMP 的理论基础 | 必须作为基线 |
| B | 日内温度模型参数是否具有区域差异 | Wann et al. (1985), *Evaluation and calibration of three models for daily cycle of air temperature* | 支撑区域化参数校准 | 强依据 |
| C | 简单 sine-exponential 模型是否存在结构局限 | Ephrath et al. (1996), *Modelling diurnal patterns of air temperature...* | 支撑引入 Tmax 时刻、辐射/大气状态等改进 | 强依据 |
| D | Parton–Logan 能否进一步修正 | Felber et al. (2018), *Generic calibration of a simple model of diurnal temperature variations...* | 提供改进 PL 和跨日连续性的直接技术路线 | 优先参考 |
| E | 干燥、大 DTR 条件下不同小时温度模型表现 | Bal et al. (2023), *Identifying appropriate prediction models for estimating hourly temperature over diverse agro-ecological regions of India* | 支撑在干燥高 DTR 环境下重新比较算法 | 优先参考 |
| F | 新疆作物系统是否存在明确温度敏感性 | 新疆玉米/DSSAT 高温及昼夜温差相关研究 | 建立区域应用背景 | 继续补文献 |

---

## 3. DSSAT 源码矩阵

已核实 DSSAT 官方开源仓库 `DSSAT/dssat-csm-os`。

官方源码 `Weather/HMET.for` 中：

- `HMET` 负责生成小时温度、小时辐射等亚日尺度气象变量；
- `HTEMP` 明确注明使用 Parton and Logan (1981)；
- `TAIRHR(TS)` 为小时气温；
- `TGRO(H) = TAIRHR(H)`，小时温度继续传递到植物模块；
- `TS = 24`，即 24 个小时步；
- `HTEMP` 当前使用固定参数：`A=2.0, B=2.2, C=1.0`；
- 源码注释明确指出 `Only today's TMAX,TMIN,SNUP,SNDN are used.`。

| 环节 | 官方源码/对象 | 关键输入 | 关键输出 | 当前机制 | DSSAT-DTR 拟研究内容 |
|---|---|---|---|---|---|
| 日气象输入 | Weather / input modules | TMAX, TMIN, SRAD 等 | 日尺度天气 | 原始天气输入 | 原则上保持不变 |
| 小时温度重构 | `Weather/HMET.for::HTEMP` | DAYL, HS, SNDN, SNUP, TMAX, TMIN | TAIRHR | Parton–Logan，A/B/C 固定 | 核心改造点 |
| 小时天气汇总 | `Weather/HMET.for::HMET` | TAIRHR | TAVG, TDAY, TGRO | 24 小时汇总 | 检查误差传播 |
| 作物温度输入 | Plant modules | TGRO / TAVG / TDAY | 温度响应 | 作物模块各自调用 | 建立完整调用链 |
| 物候 | CERES-Maize `MZ_PHENOL.for` 等 | 温度、热时间 | 生育阶段 | 当前 DSSAT 热时间机制 | 检查 DTR 误差传播 |
| 生长/产量 | CERES-Maize `MZ_GROSUB.for` 等 | 温度、生育状态 | 生物量/产量 | 当前 DSSAT 生长机制 | 第二阶段研究 |

---

## 4. 第一阶段模型矩阵

先只解决“DSSAT 能否正确恢复新疆小时温度”，暂不同时修改所有作物过程。

| 模型 | 小时温度方案 | 目的 |
|---|---|---|
| M0 | DSSAT 原始 HTEMP：PL，A=2.0/B=2.2/C=1.0 | 官方基线 |
| M1 | PL-XJ：仍使用 Parton–Logan，但 A/B/C 用新疆实测小时温度校准 | 检验区域参数问题 |
| M2 | Improved-PL：参考 Felber 等对相位、跨日 Tmin 等进行修正 | 检验结构改进 |
| M3 | Alternative sub-daily model：参考 Bal 等筛选三阶段或其他模型 | 算法竞争基线 |

原则：只有 M1 明显改善，说明主要是区域参数问题；M2/M3 进一步显著改善，才有依据提出结构性温度模块改进。

---

## 5. 温差分层验证矩阵

每天计算：

`DTR = TMAX - TMIN`

建议首先使用以下分组，并根据新疆样本分布调整：

- DTR < 10 °C
- 10 ≤ DTR < 15 °C
- 15 ≤ DTR < 20 °C
- DTR ≥ 20 °C

每组比较：

- RMSE
- MAE
- Bias / MBE
- R²
- Tmax 出现时刻误差
- Tmin 出现时刻误差
- 日间 RMSE
- 夜间 RMSE

同时检查：随着 DTR 增加，M0 误差是否系统扩大。

---

## 6. 第二阶段作物传播矩阵

只有第一阶段证明温度模块确实存在系统偏差后，再进入 DSSAT 作物过程。

| 层级 | 指标 | 目的 |
|---|---|---|
| 温度 | hourly T RMSE/MAE/Bias | 证明温度重构改善 |
| 热时间 | DTT / accumulated thermal time | 证明温度误差进入热时间 |
| 物候 | emergence / anthesis / silking / maturity 日期误差 | 证明生育进程改善 |
| 冠层 | LAI | 检查生长过程 |
| 生物量 | biomass | 检查物质形成 |
| 产量 | grain yield | 最终应用结果 |

---

## 7. 用户需要准备的数据

### 必需数据 A：逐小时气温

这是整个研究最优先的数据。

理想形式：

| datetime | station | temperature_C |
|---|---|---:|
| 2020-06-01 00:00 | XXX | 12.4 |
| ... | ... | ... |

要求：

- 新疆研究区或尽可能邻近作物试验区；
- 至少覆盖多个完整生长季；
- 必须能从逐小时数据独立计算每日 Tmax/Tmin；
- 数据源、站点位置、时间分辨率和质量控制信息要可追溯。

ERA5-Land hourly 可以作为补充/空间扩展，站点实测优先用于主验证。

### 必需数据 B：DSSAT 玉米试验/生产数据

第二阶段需要：

- 播种日期；
- 品种；
- 开花/吐丝/成熟日期，能获得多少保留多少；
- 最终产量；
- 有条件时增加 LAI、生物量；
- 灌溉、施肥、土壤等 DSSAT 常规驱动数据。

### 必需数据 C：现有 DSSAT 工程

如果已经建好新疆 DSSAT-CERES-Maize 工程，保留：

- Experiment files；
- Weather files；
- Soil files；
- Cultivar/Ecotype 参数；
- Management 设置；
- 当前校准和验证结果。

---

## 8. 用户当前不需要做的事情

- 不需要自行修改 Fortran 源码；
- 不需要先人为调整 Tmax/Tmin；
- 不需要先设定一个“新疆温差修正系数”；
- 不需要同时改物候、光合、呼吸、产量全部过程；
- 不需要一开始追求产量拟合提升。

第一目标只有一个：用真实小时温度验证 DSSAT `HTEMP` 在新疆高 DTR 条件下究竟有没有结构性问题。

---

## 9. 下一步源码审查任务

1. 完整追踪 `TMAX/TMIN -> HTEMP -> TAIRHR -> TGRO -> CERES-Maize` 调用链。
2. 标出 CERES-Maize 中所有读取 `TGRO/TAVG/TDAY/TMAX/TMIN` 的位置。
3. 区分：物候温度、光合作用温度、呼吸温度、高温胁迫、低温胁迫。
4. 建立变量级 DAG，明确改 `HTEMP` 后哪些结果会自然变化。
5. 保持原始 DSSAT executable 作为 M0，所有实验只在独立分支编译修改版。

---

## 10. 当前研究定位

建议暂定题目：

**Regional evaluation and improvement of the sub-daily temperature reconstruction scheme in DSSAT-CERES-Maize for arid continental environments with large diurnal temperature ranges**

中文：

**新疆干旱大陆性气候条件下 DSSAT-CERES-Maize 日内温度重构机制的区域适应性评价与改进**

当前阶段不提前宣称“DSSAT 存在缺陷”。论文证据顺序必须是：

`真实逐小时温度 -> 原始 HTEMP 误差诊断 -> DTR 分层 -> 改进算法 -> 热时间传播 -> 物候/产量验证`。
