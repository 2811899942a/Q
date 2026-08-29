# DSSAT-DTR 乌鲁木齐市公开数据方案

## 1. 固定研究范围

DSSAT-DTR 数据工作仅围绕乌鲁木齐市展开。

- 总边界：乌鲁木齐市行政区全域；
- 核心气象站：51463099999（87.6167°E, 43.7833°N, 919 m）；
- DSSAT 农业模拟：乌鲁木齐市域内实际农作物种植/灌溉区；
- 第一阶段目标：验证 DSSAT `HTEMP` 在乌鲁木齐大昼夜温差条件下的小时温度重构误差；
- 第二阶段目标：将改进温度过程传递到玉米物候和产量模拟。

## 2. 足够支撑研究的数据组合

### A. 51463099999 NOAA Global Hourly / ISD

用途：DSSAT `HTEMP` 的主要观测验证数据。

官方来源：
- https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
- https://www.ncei.noaa.gov/access/search/datasets/global-hourly/

需要字段：
- DATE（UTC 时间）；
- TMP（气温）；
- QUALITY_CONTROL / TMP质量标志；
- station metadata。

处理：
1. UTC -> CST (UTC+8)；
2. 解析 TMP 为 °C；
3. 去除缺测及明显坏质量值；
4. 计算每天有效温度观测数；
5. 计算观测日 Tmax、Tmin、DTR；
6. 按实际存在的观测时刻比较 DSSAT `HTEMP`，避免把3小时/6小时观测误称为完整24小时观测；
7. 对 DTR 分层统计 RMSE、MAE、MBE、R²；
8. 单独统计白天、夜间误差及 Tmax/Tmin 出现时间误差。

建议初始时间范围：2000-2024；与现有项目水文数据时间段一致。作物试验传播验证重点使用 2021-2022。

### B. ERA5-Land Hourly

用途：乌鲁木齐市域连续小时温度场、51463缺测补充、空间扩展；不作为替代站点观测的唯一“真值”。

Google Earth Engine：
`ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')`

官方目录：
https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY

关键变量：
- `temperature_2m`；
- 可同时保留 `surface_solar_radiation_downwards_hourly` 等温度机制解释变量。

处理：
1. 51463 点位提取小时序列；
2. 转换 K -> °C；
3. UTC -> CST；
4. 与 NOAA 观测逐时匹配；
5. 后续使用乌鲁木齐行政边界裁剪全市小时/日DTR场。

### C. 乌鲁木齐安宁渠玉米公开田间试验（主作物验证）

论文：Tang et al. (2024), *Assessing the Influence of Planting Dates on Sustainable Maize Production under Drought Stress Conditions*, Sustainability 16, 4571.
DOI: 10.3390/su16114571
来源：https://www.mdpi.com/2071-1050/16/11/4571

试验位置：Anningqu, Urumqi，约 87.49°E, 43.95°N, 590 m。
年份：2021、2022。

公开信息包括：
- 多个玉米品种；
- 5个播期/温度处理层次；
- 6个梯度灌溉水平，共30个处理组合；
- 随机区组、3次重复；
- 抽雄/开花相关物候；
- 产量及产量构成；
- 生育期温度、降雨、蒸发背景。

用途：
- 第二阶段 CERES-Maize 校准/验证候选数据；
- 重点验证播期变化导致的温度暴露差异能否被 DSSAT-DTR 更好描述；
- 物候（尤其抽雄/吐丝）和最终产量作为温度改进向作物过程传播的证据。

### D. 乌鲁木齐三坪农场冬小麦公开试验（备选，不作为当前主线）

论文：*Wide-narrow row planting and limited irrigation improve grain filling and spike traits in winter wheat in arid regions*, Scientific Reports (2025).
来源：https://www.nature.com/articles/s41598-025-00889-4

位置：Sanping Farm, Toutunhe District, Urumqi。
试验期：2021-2023。
公开信息包含土壤、灌溉处理、灌浆、生物量/穗部性状及产量。

仅在研究内容2最终需要同时做冬小麦时启用；当前 DSSAT-DTR 源码验证先以玉米为主。

## 3. 第一阶段最小充分数据集

当前只需要真正拿齐下面三项：

1. `51463099999`：2000-2024 小时/天气观测；
2. ERA5-Land：51463点位 2000-2024 小时温度；
3. 安宁渠玉米：2021-2022 试验设计 + 播期 + 灌溉 + 物候 + 产量。

以上三项已经足以完成：

`真实/准真实小时温度 -> DSSAT HTEMP误差诊断 -> DTR分层 -> PL参数区域化/结构改进 -> 玉米物候与产量传播验证`

暂不继续扩张新疆其他站点和其他流域。

## 4. 数据质量闸门

### NOAA 51463

每天按有效气温观测数分级：
- A：>=20条/日，可用于完整日内曲线与日极值验证；
- B：8-19条/日，可在观测时刻验证 HTEMP，日极值需谨慎；
- C：4-7条/日，仅用于辅助；
- <4：剔除当天。

正式分析必须先报告每年 A/B/C 天数，确认 51463 实际观测频率。

### 作物试验

所有从论文表格/图中整理的数据必须标记：
- `table-derived`；
- `figure-derived`；
- `supplement-derived`；
- `raw-open`（若后续找到原始附件）。

论文图表数据用于模型验证时保留原始出处、单位、处理编号和年份，不混合不同处理。

## 5. 当前决策

- 主气象真值：NOAA 51463099999；
- 连续小时背景：ERA5-Land；
- 主作物验证：乌鲁木齐安宁渠 2021-2022 玉米；
- 冬小麦：三坪农场作为后备；
- 不再扩展奇台、石河子等新疆其他地区作为正式主数据。
