# DSSAT 新疆区域温度优化：最佳结果与创新流程（Canonical Final）

> 日期：2026-09-05  
> 基线：DSSAT v4.8.5 / CERES-Maize  
> 分支：`research/dssat-regional-dtr-joint-v1`  
> Source commit：`0b91373806786b600d89ccfcfff78fa2f82cb26b`  
> Data commit：`79cb5db71bbca186add92a6a9695866a09c8b51d`

## 1. 最终研究定位

当前成果应拆成三个互补部分：

- **M17b：小时温度拟合性能基准。** 负责回答“官方 HTEMP 在目标气候条件下还有多少可优化空间”。
- **M19：区域参数架构。** 新增可跨地区重新率定的区域热异常阈值 `K_RT`。
- **M20：作物模型传播桥。** 将 M19 引起的小时热时间增量，以中性方式接入 CERES-Maize 的 DTT（日热时间）累积。

论文主创新建议固定为：

> **M19 区域热异常阈值 `K_RT` + M20 中性增量 DTT 桥接。**

M17b 保留为温度层性能证据，不把撞上边界的形状系数包装成新疆区域参数。

---

## 2. 当前最佳小时温度结果：M17b

官方 HTEMP 与 M17b 的验证结果：

| 指标 | 官方 HTEMP | M17b | 改善 |
|---|---:|---:|---:|
| 总体 RMSE | 2.946891 ℃ | **2.583205 ℃** | **12.34%** |
| DTR≥15 ℃ RMSE | 5.121512 ℃ | **4.376778 ℃** | **14.54%** |
| 高DTR物理违规 | — | **0/123** | PASS |
| 2020—2024逐年胜出 | — | **5/5** | PASS |

高DTR逐年 RMSE：

| 年份 | 官方 HTEMP | M17b |
|---|---:|---:|
| 2020 | 5.182119 | **4.481581** |
| 2021 | 5.097851 | **4.356101** |
| 2022 | 4.795950 | **4.218852** |
| 2023 | 4.976799 | **3.968663** |
| 2024 | 5.456594 | **4.753991** |

M17b 的 `k_pre`、`k_post` 扩展到 40 后仍达到搜索上界，说明曲线变形需求很强，同时参数识别尚未稳定。因此它进入“性能上限基准”，不进入最终区域参数定义。

---

## 3. 为什么把核心作物接口放在 DTT

前期真实 DSSAT 机制筛选显示：

| 扰动 | 平均产量变化 | 主要意义 |
|---|---:|---|
| TMAX +1 ℃ | −472.67 kg/ha | 高温通道敏感 |
| TMAX +4 ℃ | −2515.67 kg/ha | 强非线性高温响应 |
| DTT ×0.95 | +553.17 kg/ha | 热时间通道高敏感 |
| DTT ×1.05 | −521.33 kg/ha | ±5% 已产生约0.5 t/ha量级变化 |
| DTT ×1.15 | −1923.50 kg/ha | 物候和产量均明显响应 |

TMIN 扰动同时改变冷胁迫、热量积累和生育期长度，因此后续正式敏感性分析需要将低温直接效应与 DTT 间接效应拆开。

早期 PRFT-only `KT` 方案最好仅使产量 RMSE 改善约 **0.033%**，已经降级。

结论：**DTT 是区域小时温度信息进入 CERES-Maize 物候和生长过程的高杠杆接口。**

---

## 4. 新区域参数：M19 的 `K_RT`

### 4.1 定义

`K_RT`：Regional Thermal Anomaly Threshold，区域热异常触发阈值，单位为当地同期 DTR 标准差（SD）。

先建立目标地区逐日气候态：

```text
mu_DTR(DOY)    = 当地多年同期平均日较差
sigma_DTR(DOY) = 当地多年同期日较差标准差
z_DTR          = [DTR - mu_DTR(DOY)] / sigma_DTR(DOY)
```

区域暴露量：

```text
E = max(z_DTR - K_RT, 0)
  * max(Kt0 - Kt, 0) / 0.1
```

有界响应：

```text
S = 1 - exp(-E / gain_scale)
q_new = (1-S)*q_official + S*q_official^P_TARGET
```

当前结构常数：

```text
Kt0        = 0.70
P_TARGET   = 20.0
gain_scale = 0.25
```

乌鲁木齐探索性结果：

```text
K_RT = 1.40 SD
```

### 4.2 M19结果

| 指标 | 官方 HTEMP | M19 |
|---|---:|---:|
| 总体 RMSE | 2.9469 ℃ | **2.8338 ℃** |
| 高DTR RMSE | 5.1215 ℃ | **4.7423 ℃** |
| 高DTR物理违规 | — | **0/123** |
| 2020—2024逐年胜出 | — | **5/5** |
| 关闭触发最大闭合误差 | — | **0.000e+00 ℃** |
| `K_RT` | — | **1.40 SD，搜索区间内部** |

M19 的优势集中在可解释性和区域迁移：换地区时重新计算当地 `mu_DTR`、`sigma_DTR`，再率定一个 `K_RT`，结构保持固定。

---

## 5. 源码审计带来的关键修正

官方天气链：

```text
WEATHR -> HMET -> HTEMP -> TAIRHR/TGRO
```

源码和真实 A/B 共同证明，DSSAT v4.8.5 的 CERES-Maize 主通道在 `MZ_CERES/MZ_PHENOL` 中使用日尺度 `TMAX/TMIN/SRAD/DAYL`，天气模块生成的 `TAIRHR/TGRO` 没有直接进入玉米物候和生长主计算。

M0/M15/M19 三套源码独立编译并完成 30/30 次 DSSAT 运行后：

```text
M15 vs M0：0/10 作物情景变化
M19 vs M0：0/10 作物情景变化
```

同时 M19 激活诊断显示：

```text
2021年5—9月：6个激活日
2022年5—9月：2个激活日
```

因此天气端算法实际已经启动，0作物响应来自源码接口缺口。这个发现直接推动 M20。

---

## 6. M20：中性小时温度—DTT桥

核心公式：

```text
DTT_M20 = DTT_official
        + K_LINK * [TT24(TAIRHR_M19) - TT24(TAIRHR_HTEMP)]
```

其中：

```text
TT24(T) = mean_h[clip(T_h,TBASE,DOPT)-TBASE], h=1...24
K_LINK = 1.0
```

`K_LINK=1.0` 固定为结构常数，不增加第二个地区率定参数。

当 M19 未触发：

```text
TAIRHR_M19 = TAIRHR_HTEMP
Delta_TT   = 0
DTT_M20    = DTT_official
```

因此官方 CERES-Maize DTT 始终保留为基线，新模块只传递由区域小时温度修正新增的热时间差。

源码位置：

- `Weather/HMET.for`：官方 HTEMP 后执行 M19；
- `Plant/CERES-Maize/MZ_CERES.for`：向 `MZ_PHENOL` 传递现有 `TAIRHR`；
- `Plant/CERES-Maize/MZ_PHENOL.for`：在官方 DTT 累积前加入 `Delta_TT`；
- 后续 `SUMDTT/CUMDTT` 沿用官方路径。

补丁：

`research/dssat_dtr/dssat485/apply_m20_dtt_bridge_patch.py`

---

## 7. M20全源码因果试验：PASS

Linux GitHub Actions：`33956296856`，**SUCCESS**。

执行量：

```text
M0 / M19 / M20 三套独立源码
自然天气：10情景 x 3 = 30 runs
受控高DTR：10情景 x 3 = 30 runs
总计：60/60 DSSAT runs
```

### 自然天气

| 模型 | 变化情景 | 平均产量差 | 最大绝对产量差 | 平均成熟差 |
|---|---:|---:|---:|---:|
| M19 vs M0 | 0/10 | 0 | 0 | 0 d |
| **M20 vs M0** | **10/10** | **−0.5 kg/ha** | **4 kg/ha** | **0 d** |

### 受控高DTR压力试验

M0/M19/M20 使用完全相同的输入天气，只在 DOY 121—273 将 TMAX 统一提高 4 ℃。

| 模型 | 变化情景 | 平均产量差 | 产量差范围 | 最大绝对差 | 平均成熟差 |
|---|---:|---:|---:|---:|---:|
| M19 vs M0 | 0/10 | 0 | 0 | 0 | 0 d |
| **M20 vs M0** | **10/10** | **−9.8 kg/ha** | **−224～+208 kg/ha** | **224 kg/ha** | **+0.2 d** |

代表情景：

- 2021-04-21播种：+138 kg/ha；
- 2021-04-26播种：+208 kg/ha；
- 2022-04-26播种：−224 kg/ha；
- 2022-05-16播种：−202 kg/ha，成熟约+1 d。

这些正负方向暂不解释为新疆真实增产或减产。该组使用代理品种和人为压力天气，承担“源码因果传播验证”角色。

能够严谨确认的结论是：

> **M19小时温度信号经过M20中性DTT桥后，已经能够稳定进入CERES-Maize，并在热异常增强时产生更明显的物候、生物量和产量响应。**

---

## 8. 完整创新流程

```text
目标地区多年 TMAX/TMIN
        |
        v
逐DOY DTR气候态：mu_DTR / sigma_DTR
        |
        v
当天 z_DTR
        |
        v
区域参数 K_RT：异常超过多少SD才启动
        |
        +--------------------+
        |                    |
        v                    v
    DTR异常强度          辐射状态 Kt
        |                    |
        +---------+----------+
                  v
            区域暴露 E
                  |
                  v
             有界响应 S
                  |
                  v
      官方 HTEMP 24h曲线
                  + M19物理约束修正
                  |
                  v
            TAIRHR_M19
                  |
          +-------+-------+
          |               |
          v               v
 TAIRHR_HTEMP       TAIRHR_M19
          |               |
          +-------+-------+
                  v
      Delta_TT = TT24_M19 - TT24_official
                  |
                  v
      DTT_M20 = DTT_official + Delta_TT
                  |
                  v
             SUMDTT/CUMDTT
                  |
                  v
            CERES-Maize
                  |
                  v
      物候 / LAI / 生物量 / 产量
```

跨地区应用时保持 M19+M20 结构固定，重新建立当地 DTR 气候态并率定 `K_RT`。

---

## 9. 创新筛选过程

| 阶段 | 结果 | 决策 |
|---|---|---|
| PRFT-KT | 最好仅改善产量RMSE约0.033% | 降级 |
| TMAX/TMIN/DTT扰动 | Tmax和DTT高敏感 | 锁定热时间通道 |
| M17 | DTR异常×辐射能改善HTEMP | 继续 |
| M17b | 当前温度拟合最好；形状系数仍撞边界 | 性能基准 |
| M18 | 有界幅度参数仍撞上界 | 放弃幅度参数作为地区系数 |
| M19 | `K_RT=1.40 SD`，内部解；中性闭合；逐年稳定 | 区域参数晋级 |
| M19源码A/B | 30次运行成功但作物0变化 | 发现接口缺口 |
| M19激活诊断 | 生长季确有触发 | 锁定接口原因 |
| M20 | 60次真实DSSAT A/B全链PASS | 源码机制闭环 |

这套筛选过程本身也是研究可信度的重要组成：候选参数经过性能、边界可识别性、物理约束、源码接口和作物响应逐级筛选。

---

## 10. 与已有研究的创新边界

已有研究已经覆盖玉米高温对物候/产量的影响、热时间或高温响应修改、DSSAT-CERES-Maize在新疆的高温/HDD模拟，以及CERES-Maize的EFAST敏感性分析。因此最终创新应放在完整机制链上：

> **区域同期标准化DTR异常阈值 `K_RT` + 辐射联合触发 + HTEMP物理约束小时修正 + 保持官方DTT基线的增量热时间桥 + CERES-Maize源码传播 + 跨地区重新率定机制。**

关键参照：

- Yang H., Li Z. et al. 2023, *Remote Sensing*, DOI `10.3390/rs15123197`：DSSAT水分敏感性改进的方法学模板；
- Lizaso J.I. et al. 2018, *Field Crops Research* 216:129–140, DOI **`10.1016/j.fcr.2017.11.013`**；
- Zhang F. et al., *European Journal of Agronomy* 172, 127860, DOI `10.1016/j.eja.2025.127860`：新疆CERES-Maize高温/HDD研究；
- Tian Y. et al. 2026, *Agricultural Water Management* 328, 110311, DOI `10.1016/j.agwat.2026.110311`：CERES-Maize EFAST全局敏感性。

截至本轮公开论文/专利检索，暂未发现与上述**完整组合链**完全同构的公开方案。正式投稿或专利申请前仍需再执行一次系统检索与权利要求级对比。

---

## 11. 当前证据边界

当前已完成：

- 小时温度层性能提升；
- `K_RT` 区域参数的可解释定义；
- 中性关闭闭合；
- 物理约束检查；
- 逐年稳定性；
- M19真实触发诊断；
- CERES-Maize源码接口审计；
- M20源码编译；
- 60次Linux真实DSSAT因果A/B；
- Windows复现脚本与Windows CI实测路线。

论文级结论还需要：

1. 新疆/乌鲁木齐目标站逐小时温度；
2. 真实目标玉米品种；
3. 开花/吐丝、成熟、产量，条件允许时加入LAI/生物量；
4. EFAST或Sobol正式全局敏感性，覆盖高温、低温、DTT、`K_RT`及阶段效应；
5. 独立年份验证；
6. 至少一个跨站点/跨地区 `K_RT` 迁移试验。

当前 `K_RT=1.40 SD` 属于乌鲁木齐探索性值，尚未冻结为新疆所有站点、年份和品种的通用参数。

---

## 12. Windows本机复现

目录：

`repro/windows_dssat_temperature_v1/`

温度层：

```powershell
.\repro\windows_dssat_temperature_v1\run_temperature_only.ps1
```

完整源码层：

```powershell
.\repro\windows_dssat_temperature_v1\run_m20_bridge.ps1
```

Windows脚本会冻结同一DSSAT源码/data，建立M0/M19/M20独立源码树，自动打补丁、MinGW/gfortran编译，并执行自然天气与受控高DTR共60次A/B。

Windows GitHub Runner 首轮已经验证源码补丁和原生Fortran编译可用；首轮在官方CMake安装Unix辅助脚本步骤发生工程性失败。复现脚本已经改为直接使用成功编译的 `dscsm048.exe` 加冻结data组装运行目录，第二轮端到端测试记录在工作流 `DSSAT M20 Windows Reproduction`。

跨平台验收重点：

```text
同一公式和参数定义
同一源码插入位置
M19关闭/未触发时保持中性
M19-only不改变CERES-Maize主输出
M20在强DTR条件下产生可重复作物响应
```

Linux与Windows最后几位小数完全相同不作为必要条件。

---

## 13. 一句话创新

> **基于目标地区同期DTR气候态构建一个可重新率定的区域热异常阈值 `K_RT`，结合辐射状态控制DSSAT小时温度的物理约束修正，再通过保持官方DTT基线的增量热时间桥，将当地日内温度特征真正传递到CERES-Maize物候和产量过程。**
