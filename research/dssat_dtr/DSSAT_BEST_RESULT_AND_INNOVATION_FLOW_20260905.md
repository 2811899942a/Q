# DSSAT 新疆区域温度优化：当前最佳结果与创新流程

> 状态：2026-09-05 源码机制阶段收口版  
> 分支：`research/dssat-regional-dtr-joint-v1`  
> 基线：DSSAT v4.8.5 / CERES-Maize  
> DSSAT source commit：`0b91373806786b600d89ccfcfff78fa2f82cb26b`  
> DSSAT data commit：`79cb5db71bbca186add92a6a9695866a09c8b51d`

---

## 1. 当前结论先行

截至 2026-09-05，温度优化路线已经形成三类互补证据：

1. **M17b：当前温度拟合性能最好的方案。**  
   相对官方 HTEMP，总体小时温度 RMSE 从 2.9469 ℃ 降至 2.5832 ℃，改善 **12.34%**；高日较差（DTR≥15 ℃）RMSE 从 5.1215 ℃ 降至 4.3768 ℃，改善 **14.54%**；2020—2024 五个年度高DTR RMSE 全部优于官方；123 个高DTR验证日出现 **0 个温度曲线物理违规**。其两个形状系数均继续顶到扩展后的搜索上界约 40，参数可识别性不足，因此保留为**性能上限/温度拟合基准**。

2. **M19：当前区域迁移参数定义最好的方案。**  
   将区域参数重新定义为**区域热异常阈值 `K_RT`**：当地某日 DTR 相对该地区同期气候态超过多少个标准差后，区域修正开始生效。当前乌鲁木齐实验得到 `K_RT = 1.40 SD`，位于搜索区间内部；关闭触发后与官方 HTEMP 的最大绝对差为 **0.000e+00 ℃**；123 个高DTR日物理违规仍为 0；2020—2024 五个年度均优于官方。其温度RMSE改善幅度低于M17b，但参数含义清晰、单位统一、具备跨地区重新率定的条件，因此作为**最终区域参数架构候选**。

3. **M20：当前源码创新链的关键闭环。**  
   DSSAT v4.8.5 源码审计发现，CERES-Maize 主程序使用日尺度 `TMAX/TMIN/SRAD/DAYL` 驱动物候和生长，天气模块中的 `TAIRHR/TGRO` 小时温度没有直接进入 `MZ_PHENOL/MZ_GROSUB`。因此仅修改 HTEMP 虽然可以改善小时温度曲线，却不能自动改变 CERES-Maize 输出。M20 新增一个**中性热时间桥接项**，只把 M19 相对于官方 HTEMP 新增的小时热时间差加入官方 DTT（日热时间）中。GitHub 全源码 A/B 已经完成，受控高DTR条件下 M20 对 10/10 个作物情景产生可重复响应，证明“区域小时温度修正 → DTT → CERES-Maize”因果链在真实 DSSAT 4.8.5 源码中成立。

因此，当前推荐的论文主线为：

> **M19 区域热异常阈值 `K_RT` + M20 中性 DTT 桥接** 作为核心创新方法；  
> **M17b** 作为小时温度优化能力的性能上限证据；  
> 后续以新疆/乌鲁木齐真实作物物候和产量数据完成区域校准、敏感性分析与独立验证。

---

## 2. 为什么研究路线最终落到 DTT

前期按照“高温—低温—积温”三个方向做了独立扰动筛选。UFGA8201 仅作为可复现的 DSSAT 机制基准，其结果用于判断模型通道敏感度，不用于替代新疆作物验证。

| 扰动 | 平均产量变化 | 物候变化 | 机制判断 |
|---|---:|---:|---|
| TMAX +1 ℃ | −472.67 kg/ha | 开花/成熟提前数日 | 高温通道具有明显杠杆效应 |
| TMAX +4 ℃ | −2515.67 kg/ha | 开花约提前6 d、成熟约提前9 d | 响应强且呈非线性 |
| TMIN −1 ℃ | +569.50 kg/ha | 生育期延长 | 同时混合低温生理效应与热时间减慢，不能直接解释为“低温增产” |
| TMIN −4 ℃ | +1705.00 kg/ha | 开花约推迟12 d、成熟约推迟15 d | 混杂效应进一步增强 |
| DTT ×0.95 | +553.17 kg/ha | 开花/成熟约推迟6 d | 热时间通道高度敏感 |
| DTT ×1.05 | −521.33 kg/ha | 开花/成熟提前数日 | ±5% 已足以改变产量约0.5 t/ha |
| DTT ×1.15 | −1923.50 kg/ha | 明显提前 | DTT 是最适合承接区域温度信息的直接作物通道 |

这组结果给出两个关键判断：

- Tmax 与日内温度过程值得继续做区域修正；
- **DTT 是把气象层温度优化传递到 CERES-Maize 物候和产量的高杠杆接口。**

PRFT-only 的早期 `KT` 指数方案最好仅改善产量 RMSE 约 0.033%，因此已经降级，不再作为论文核心。

---

## 3. 当前最佳小时温度结果：M17b

### 3.1 公式思想

M17/M17b 使用区域 DTR 异常与太阳辐射状态共同决定温度曲线变形强度：

```text
E = max(z_DTR - q, 0) * max(Kt0 - Kt, 0) / 0.1
```

其中：

- `DTR = TMAX - TMIN`；
- `z_DTR` 为当地同期标准化日较差异常；
- `Kt` 表示日太阳辐射相对天文可能辐射的状态；
- 变形只作用于官方 HTEMP 生成的日内温度曲线肩部，并受 Tmin/Tmax 与单调性物理约束。

### 3.2 定量结果

| 指标 | 官方 HTEMP | M17b | 改善 |
|---|---:|---:|---:|
| 总体 RMSE | 2.946891 ℃ | **2.583205 ℃** | **12.34%** |
| DTR≥15 ℃ RMSE | 5.121512 ℃ | **4.376778 ℃** | **14.54%** |
| 高DTR全曲线物理违规 | — | **0/123** | PASS |
| 2020—2024逐年高DTR胜出 | — | **5/5** | PASS |

逐年高DTR RMSE：

| 年份 | 官方 HTEMP | M17b |
|---|---:|---:|
| 2020 | 5.182119 | **4.481581** |
| 2021 | 5.097851 | **4.356101** |
| 2022 | 4.795950 | **4.218852** |
| 2023 | 4.976799 | **3.968663** |
| 2024 | 5.456594 | **4.753991** |

### 3.3 为什么 M17b 暂时不作为最终区域参数

扩展搜索范围后 `k_pre≈40`、`k_post≈40` 仍同时达到上界。该结果说明温度拟合确实持续偏好更强的曲线变形，但“最优形状系数是多少”尚未形成稳定可识别的参数估计。直接把约40作为“新疆系数”缺少充分依据。

因此 M17b 的最合理角色是：

> **证明官方 HTEMP 在目标气候条件下存在可优化空间，并给出当前最高性能参考。**

---

## 4. 最有迁移价值的新参数：M19 的 `K_RT`

### 4.1 参数定义

`K_RT` 定义为：

> **Regional Thermal Anomaly Threshold：区域热异常触发阈值，单位为当地同期 DTR 标准差（SD）。**

首先根据目标地区多年资料建立逐日气候态：

```text
mu_DTR(d)     = 第 d 个年内日序的多年平均 DTR
sigma_DTR(d)  = 第 d 个年内日序的多年 DTR 标准差
```

当天标准化异常：

```text
z_DTR = [DTR - mu_DTR(DOY)] / sigma_DTR(DOY)
```

区域修正暴露量：

```text
E = max(z_DTR - K_RT, 0)
  * max(Kt0 - Kt, 0) / 0.1
```

当前结构常数：

```text
Kt0        = 0.70
P_TARGET   = 20.0
gain_scale = 0.25
```

有界响应：

```text
S = 1 - exp(-E / gain_scale)
q_new = (1-S)*q_official + S*q_official^P_TARGET
```

当前乌鲁木齐探索性标定：

```text
K_RT = 1.40 SD
```

### 4.2 为什么这个参数比“固定温度阈值”更适合区域迁移

`K_RT` 使用标准差单位描述“相对于当地正常日较差到底异常到什么程度”。因此不同地区可采用同一模型结构：

1. 用本地多年温度建立 `mu_DTR(DOY)` 与 `sigma_DTR(DOY)`；
2. 用本地小时温度/作物观测重新率定一个 `K_RT`；
3. 保持 M19/M20 的结构形式固定；
4. 比较不同地区 `K_RT` 与最终作物响应。

这比直接规定“DTR=13.5 ℃或13.8 ℃以后触发”具有更好的气候学可解释性。13.5/13.8 ℃可保留为前期 DTR 诊断信息，不再承担核心创新参数角色。

### 4.3 M19 当前结果

| 指标 | 官方 HTEMP | M19 | 结果 |
|---|---:|---:|---:|
| 总体 RMSE | 2.9469 ℃ | **2.8338 ℃** | 改善3.84% |
| 高DTR RMSE | 5.1215 ℃ | **4.7423 ℃** | 改善7.40% |
| 高DTR物理违规 | — | **0/123** | PASS |
| 2020—2024逐年胜出 | — | **5/5** | PASS |
| 关闭触发最大闭合误差 | — | **0.000e+00 ℃** | PASS |
| `K_RT` | — | **1.40 SD** | 位于搜索区间内部 |

M19 的研究价值集中于**参数定义、可迁移性和中性闭合**，温度拟合极值由M17b提供参考。

---

## 5. 源码审计发现的关键接口问题

最初设想的链条为：

```text
TMAX/TMIN -> HTEMP -> TAIRHR/TGRO -> CERES-Maize -> yield
```

实际 DSSAT v4.8.5 源码审计显示：

- `WEATHR -> HMET -> HTEMP` 确实生成小时 `TAIRHR/TGRO`；
- `MZ_CERES.for` 读取 `TMAX/TMIN/SRAD/DAYL` 等日变量；
- `MZ_PHENOL.for` 使用日尺度 TMAX/TMIN 计算 CERES-Maize DTT；
- `TAIRHR/TGRO` 没有直接传入 CERES-Maize 的 `MZ_PHENOL/MZ_GROSUB` 主通道。

该接口事实由真实 A/B 进一步验证：

- M0/M15/M19 三套源码均独立编译成功；
- 10个安宁渠情景×3模型，共30次 DSSAT 运行全部完成；
- M15 vs M0：0/10 作物情景变化；
- M19 vs M0：0/10 作物情景变化。

随后单独检查 M19 是否真的在安宁渠天气中触发：

- 2021年5—9月：**6个激活日**；
- 2022年5—9月：**2个激活日**；
- 2021各播期窗口：5—8个激活日；
- 2022各播期窗口：均为2个激活日。

由此确认：M19 天气端工作正常，作物输出为0源于 CERES-Maize 的接口结构。

这个审计结果直接催生了 M20。

---

## 6. M20：中性小时温度—DTT桥接

### 6.1 核心公式

M20 保留 CERES-Maize 官方 DTT 计算作为基线，仅加入 M19 相对于官方 HTEMP 产生的**小时热时间增量**：

```text
DTT_M20 = DTT_official
        + K_LINK * [TT24(TAIRHR_M19) - TT24(TAIRHR_HTEMP)]
```

其中：

```text
TT24(T) = mean_h[ clip(T_h, TBASE, DOPT) - TBASE ], h=1...24
K_LINK = 1.0
```

`K_LINK=1.0` 是固定结构常数，不作为新的区域率定参数。

### 6.2 最重要的中性性质

当 M19 不触发：

```text
TAIRHR_M19 = TAIRHR_HTEMP
```

因此：

```text
TT24(TAIRHR_M19) - TT24(TAIRHR_HTEMP) = 0
```

最终：

```text
DTT_M20 = DTT_official
```

这样可以保证新模块只传递“区域温度修正新增的热时间信息”，不会整体覆盖 CERES-Maize 已有的热时间算法。

### 6.3 源码位置

M20 实际修改：

1. `Weather/HMET.for`：保留官方 HTEMP，并执行 M19 小时曲线修正；
2. `Plant/CERES-Maize/MZ_CERES.for`：将现有 `Weather%TAIRHR` 以及日出/日落状态传给 `MZ_PHENOL`；
3. `Plant/CERES-Maize/MZ_PHENOL.for`：在官方 DTT 累积前重新构造官方 HTEMP 参考小时曲线，计算 M19 与官方的 `TT24` 差，并加入 DTT；
4. `SUMDTT/CUMDTT` 后续仍沿用 DSSAT 原有累积路径。

源码补丁：

`research/dssat_dtr/dssat485/apply_m20_dtt_bridge_patch.py`

---

## 7. M20真实 DSSAT A/B：因果链已经跑通

GitHub Actions：

`DSSAT M20 Hourly to DTT Bridge`  
Run ID：`33956296856`  
状态：**SUCCESS**

完整执行链包括：

- 冻结 DSSAT v4.8.5 源码/data；
- M0/M19/M20 三套源码；
- M19、M20补丁；
- 三套独立编译；
- 自然天气 30 次 DSSAT；
- 受控高DTR天气 30 次 DSSAT；
- 60 次运行结果解析；
- 因果门检查；
- 原始 Summary.OUT / PlantGro.OUT 审计产物上传。

### 7.1 自然安宁渠天气

| 模型 | 变化情景 | 平均产量变化 | 最大绝对产量变化 | 平均开花变化 | 平均成熟变化 |
|---|---:|---:|---:|---:|---:|
| M19 vs M0 | 0/10 | 0 | 0 | 0 d | 0 d |
| **M20 vs M0** | **10/10** | **−0.5 kg/ha** | **4 kg/ha** | **0 d** | **0 d** |

自然年份中 M19 激活日较少，因此 DTT 桥接对最终产量的影响很小；10/10 情景均出现可重复输出变化已经证明桥接进入 CERES-Maize 计算链。

### 7.2 受控高DTR因果压力试验

为检验更强温度异常下的传递能力，M0/M19/M20 三个模型使用完全相同的修改后天气：DOY 121—273 统一将 TMAX 增加 4 ℃。这一组属于机制压力试验，不作为真实气候情景或产量验证。

| 模型 | 变化情景 | 平均产量变化 | 产量变化范围 | 最大绝对产量变化 | 平均成熟变化 |
|---|---:|---:|---:|---:|---:|
| M19 vs M0 | 0/10 | 0 | 0 | 0 | 0 d |
| **M20 vs M0** | **10/10** | **−9.8 kg/ha** | **−224 ～ +208 kg/ha** | **224 kg/ha** | **+0.2 d** |

代表性情景：

- 2021-04-21 播种：产量 **+138 kg/ha**；
- 2021-04-26 播种：产量 **+208 kg/ha**；
- 2022-04-26 播种：产量 **−224 kg/ha**；
- 2022-05-16 播种：产量 **−202 kg/ha**，成熟约推迟1 d；
- 其余情景也出现生物量、HI或LAI的小幅响应。

这里无需把正负方向解释成“区域修正一定增产/减产”。当前固定代理品种和受控天气用于回答单一问题：

> **区域小时温度信号经过中性 DTT 桥以后，能否真实进入 CERES-Maize 并改变作物状态？答案已经是 PASS。**

---

## 8. 最终创新流程

### 8.1 从输入到作物输出的完整链

```text
逐日 TMAX / TMIN / SRAD / DOY / 纬度
              |
              v
DTR = TMAX - TMIN
              |
              v
建立目标地区逐DOY气候态
mu_DTR(DOY), sigma_DTR(DOY)
              |
              v
z_DTR = [DTR-mu]/sigma
              |
              v
区域参数 K_RT
“偏离当地同期正常状态多少SD才触发”
              |
              +--------------------+
              |                    |
              v                    v
       z_DTR - K_RT          辐射状态 Kt
              |                    |
              +---------+----------+
                        v
               区域暴露量 E
                        |
                        v
              有界响应强度 S
                        |
                        v
官方 HTEMP 日内温度曲线
        + M19物理约束肩部修正
                        |
                        v
              TAIRHR_M19(24h)
                        |
             +----------+----------+
             |                     |
             v                     v
  TAIRHR_HTEMP(24h)       TAIRHR_M19(24h)
             |                     |
             +----------+----------+
                        v
 delta_TT = TT24_M19 - TT24_official
                        |
                        v
DTT_M20 = DTT_official + delta_TT
                        |
                        v
                SUMDTT / CUMDTT
                        |
                        v
          CERES-Maize 物候 / 生长
                        |
                        v
      开花期 / 成熟期 / LAI / 生物量 / 产量
```

### 8.2 对其他地区如何迁移

模型结构原则上保持固定，目标地区重新完成：

```text
本地多年 TMAX/TMIN
      -> 本地 mu_DTR(DOY), sigma_DTR(DOY)
      -> 本地小时温度 + 作物观测校准 K_RT
      -> M19 + M20 固定结构
      -> 独立年份/独立站点验证
```

最终可以形成地区间可比较的：

```text
K_RT(Urumqi)
K_RT(Shihezi)
K_RT(other region)
```

其物理含义统一为“当地 DTR 相对季节气候态达到多少个标准差后，区域温度过程修正开始作用”。

---

## 9. 创新是如何一步一步筛出来的

| 阶段 | 做法 | 结果 | 决策 |
|---|---|---|---|
| Phase 1 | PRFT连续指数 `KT` | 最优RMSE仅改善约0.033% | 降级 |
| Phase 2 | TMAX/TMIN/DTT独立扰动 | Tmax和DTT高敏感；DTT±5%已引起约±0.5 t/ha产量变化 | 转向热时间通道 |
| M17 | DTR异常×辐射控制HTEMP曲线 | RMSE明显改善 | 继续 |
| M17b | 扩大形状系数范围 | 当前最高温度性能；系数仍撞上界 | 保留为性能基准 |
| M18 | 有界幅度参数 `K_RT` | 参数仍撞上界 | 放弃“修正幅度”作为区域参数 |
| M19 | `K_RT` 改定义为标准化DTR异常触发阈值 | `K_RT=1.40 SD`，区间内部；中性闭合；逐年稳定 | 晋级为区域参数架构 |
| M19 source A/B | 将M19嵌入HMET/HTEMP | 三套源码30/30成功，但作物输出0变化 | 发现CERES-Maize接口缺口 |
| M19 activation | 单独查触发日 | 生长季确有激活日 | 排除“没有触发” |
| M20 | 小时热时间差桥接官方DTT | 60次DSSAT运行全链SUCCESS；受控高DTR 10/10作物响应 | 源码机制闭环 |

这个筛选过程本身非常重要：每一次模型升级都有明确的淘汰理由，最终参数来源于**可识别性、物理边界、源码接口和作物敏感性**共同约束，而不是单纯寻找最低RMSE。

---

## 10. 当前最稳妥的论文创新表述

建议暂时使用如下研究口径：

> 针对干旱内陆区显著日较差条件下 DSSAT 小时温度重建与 CERES-Maize 热时间响应之间的区域适应问题，构建基于当地季节性 DTR 气候态的标准化热异常阈值参数 `K_RT`，并将 DTR 异常与辐射状态耦合，用于约束官方 HTEMP 日内温度曲线的区域修正；进一步建立中性的小时温度—DTT热时间桥接，只将区域小时温度修正所引起的增量热时间传入 CERES-Maize，从而保持官方DTT基线并实现区域温度特征向物候和产量过程的源码级传播。

更短的汇报版：

> **新增一个可区域率定的热异常阈值参数 `K_RT`，用“当地DTR异常程度+辐射状态”决定DSSAT何时修正日内温度，再把这部分新增小时热量通过中性DTT桥传入CERES-Maize。**

---

## 11. 与已有研究的边界

当前创新不能放在以下几个单独动作上：

1. **Parton–Logan/HTEMP 小时温度重建本身**已有长期基础；
2. **DSSAT 玉米高温胁迫与热时间修改**已有 Lizaso 等 CSM-IXIM 研究，例如 DOI `10.1016/j.fcr.2017.09.019`；
3. **新疆 DSSAT-CERES-Maize 高温/HDD—产量研究**已经发表，Fangliang Zhang 等 DOI `10.1016/j.eja.2025.127860`，其结果显示吐丝—乳熟和乳熟—成熟阶段每增加1 ℃·d HDD，产量分别约下降0.6%和0.3%；
4. **CERES-Maize EFAST敏感性分析**已有 2026 Agricultural Water Management 工作，DOI `10.1016/j.agwat.2026.110311`；
5. 李增兰、杨海波等 2023 Remote Sensing（DOI `10.3390/rs15123197`）已经给出了“发现DSSAT敏感性不足—构建新胁迫因子—修改源码—验证作物输出”的优秀方法学模板。

因此当前最有辨识度的创新组合位于完整链条：

> **区域同期标准化DTR异常阈值 `K_RT`**  
> **+ 辐射状态联合触发**  
> **+ HTEMP物理约束小时曲线修正**  
> **+ 与官方DTT保持中性闭合的增量热时间桥接**  
> **+ CERES-Maize源码级传播与区域再率定机制**。

截至本轮公开论文/专利检索，**暂未发现与上述完整机制链完全同构的公开方案**。该表述仅用于当前研究定位，正式投稿/专利申请前仍需再完成一次系统检索和权利要求级对比。

---

## 12. 当前证据边界

现在已经能够严谨声明：

- M17b 对目标小时温度验证集的拟合优于官方 HTEMP；
- M19 的 `K_RT=1.40 SD` 在当前搜索中位于内部，并通过中性闭合和逐年稳定性检查；
- M19 在安宁渠自然生长季确实存在激活日；
- DSSAT v4.8.5 CERES-Maize 没有直接消费 HTEMP 生成的 `TAIRHR/TGRO`；
- M20 中性 DTT 桥已在真实 DSSAT 4.8.5 源码中编译和运行；
- M20 在自然天气和受控高DTR天气中均产生可重复作物输出变化；
- GitHub Linux端60次M0/M19/M20作物A/B因果门已PASS。

现在还不应声明：

- `K_RT=1.40` 是整个乌鲁木齐或新疆所有玉米品种的最终参数；
- M20 已经提高真实新疆产量模拟精度；
- 受控 `TMAX+4 ℃` 的产量正负变化代表真实未来气候影响；
- 当前代理品种 IB0035 可以代表目标新疆品种；
- 当前结果已经完成论文级外部验证。

---

## 13. 下一阶段论文级验证

### 13.1 区域数据

至少准备：

- 新疆/乌鲁木齐目标站点逐小时气温；
- 同期 TMAX/TMIN/SRAD 等 DSSAT 天气输入；
- 目标玉米品种；
- 播期与管理；
- 开花/吐丝期、成熟期；
- 最终产量；
- 有条件时增加 LAI/生物量。

### 13.2 正式敏感性分析

按照导师要求，最终敏感性应同时覆盖：

- 高温暴露；
- 低温暴露；
- DTT/积温；
- `K_RT`；
- 必要的生育阶段交互。

建议采用 EFAST 或 Sobol，报告一阶敏感度、总效应敏感度，并按营养生长、吐丝/开花、灌浆、成熟阶段拆分。这样可以把 Phase 2 的机制筛选升级为论文级全局敏感性结果。

### 13.3 正式 A/B

```text
M0 = 官方 DSSAT 4.8.5
M* = 仅增加 M19 + M20 温度模块
```

要求：

- 品种、土壤、播期、灌溉、施肥、天气完全一致；
- 先锁定其他参数；
- 比较小时温度、开花、成熟、LAI/生物量和产量；
- 训练/校准年份与独立验证年份分开；
- 最终增加跨站点或跨地区迁移试验。

---

## 14. Windows 本机复现

复现目录：

`repro/windows_dssat_temperature_v1/`

推荐两层执行。

### A. 温度层

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\repro\windows_dssat_temperature_v1\run_temperature_only.ps1
```

检查：

- `K_RT≈1.40 SD`；
- 关闭触发后官方闭合；
- 物理违规为0。

### B. 完整 M20 源码层

```powershell
.\repro\windows_dssat_temperature_v1\run_m20_bridge.ps1
```

脚本自动完成：

```text
冻结源码/data
-> 建立M0/M19/M20独立源码树
-> 自动源码补丁
-> MinGW/gfortran编译
-> 2021/2022自然安宁渠 30 runs
-> 完全相同的受控高DTR天气 30 runs
-> 解析 Summary.OUT / PlantGro.OUT
-> 因果门
-> manifest.json
```

Linux参考结果为 Run `33956296856`。跨平台小数误差不作为失败条件，必须保持的因果不变量为：

```text
M19-only 不改变 CERES-Maize 作物输出
M20 能把 M19 小时热时间增量传入 CERES-Maize
受控高DTR条件下 M20 至少一个、参考结果10/10情景发生响应
```

旧入口 `run_full_crop_ab.ps1` 已经改为自动转发至 M20 正式流程。

---

## 15. 关键文件索引

### 参数与结果

- `research/dssat_dtr/data/m17b_regional_radwarp_boundary_audit/`
- `research/dssat_dtr/data/m19_regional_anomaly_threshold/parameters.json`
- `research/dssat_dtr/data/m19_regional_anomaly_threshold/regional_dtr_profile_2000_2016.csv`
- `research/dssat_dtr/data/anningqu/m19_activation_diagnostic/`
- `research/dssat_dtr/data/anningqu/m20_dtt_bridge/bridge_summary.csv`
- `research/dssat_dtr/data/anningqu/m20_dtt_bridge/bridge_detail.csv`

### 源码补丁

- `research/dssat_dtr/dssat485/apply_m19_htemp_patch_2call.py`
- `research/dssat_dtr/dssat485/apply_m20_dtt_bridge_patch.py`

### 实验与解析

- `research/dssat_dtr/scripts/diagnose_m19_anningqu_activation.py`
- `research/dssat_dtr/scripts/build_controlled_dtr_weather.py`
- `research/dssat_dtr/scripts/parse_m0_m19_m20_bridge.py`

### CI

- `.github/workflows/dssat-m20-dtt-bridge.yml`
- `.github/workflows/dssat-m20-windows-repro.yml`

### 连续实验日志

- `research/dssat_dtr/EXPERIMENT_LOG_M17_M19.md`

### Windows

- `repro/windows_dssat_temperature_v1/README_WINDOWS.md`
- `repro/windows_dssat_temperature_v1/run_temperature_only.ps1`
- `repro/windows_dssat_temperature_v1/run_m20_bridge.ps1`
- `repro/windows_dssat_temperature_v1/run_full_crop_ab.ps1`

---

## 16. 当前一句话研究结论

> **当前最有价值的成果已经从“调一个更好的小时温度曲线”推进到“定义一个可跨地区重新率定的热异常阈值 `K_RT`，并用中性的增量DTT桥把区域小时温度特征真正接入 CERES-Maize”。M17b负责证明温度优化空间，M19负责区域参数，M20负责作物源码传播；三部分合在一起构成当前完整创新链。**
