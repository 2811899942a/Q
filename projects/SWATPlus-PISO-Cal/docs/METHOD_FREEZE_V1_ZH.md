# PISO-Cal 方法冻结 V1

## 核心假设

模拟数据训练的参数后验可以作为真实观测率定的候选先验。其可信度随观测与模拟分布的偏离程度下降。将该先验以受控比例注入成熟的局部序贯优化器，可能降低冷启动阶段的无效 Real-SWAT+ 调用。

## 统计结构

```text
(theta, Qsim) archive
        ↓
NPE: q_phi(theta | Qsim)
        ↓ condition on Qobs
proposal posterior
        ↓ OOD diagnostic and pre-registered trust weight
posterior/prior mixture candidates
        ↓
Real-SWAT+ and frozen observed objective
        ↓
TuRBO objective surrogate and trust region
        ↓
next batch
```

NPE自身不会通过 observed NSE 获得有监督更新。真实目标信息进入 TuRBO 和候选接受过程。这样避免向后验网络提供不存在的“真实参数标签”。

## 一轮 W6 候选

- 4个：TuRBO主目标 acquisition；
- 1个：posterior-guided候选，必须达到主目标竞争性门槛；
- 1个：不确定性/参数多样性候选。

posterior候选不满足门槛时，该名额自动由标准TuRBO候选替代。

## 决定性消融

1. TuRBO；
2. Point-Warm-TuRBO；
3. Posterior-Only；
4. PISO-Cal fixed trust；
5. PISO-Cal OOD-adaptive trust。

## 主张边界

- “在线率定更快”只依据面对 Qobs 后的新增 Real-SWAT+ 次数；
- “总成本更低”必须把生成训练模拟的成本计入；
- 单一A流域场景下，5000套离线模拟无法自然摊销；
- 总成本优势需要在250/500/1000等小训练规模下验证，或在多个率定目标上展示复用收益。
