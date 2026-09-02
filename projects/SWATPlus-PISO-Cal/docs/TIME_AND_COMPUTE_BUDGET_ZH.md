# 时间与计算预算

## 1. 估计假设

时间按以下条件估算：South Branch 正式 SWAT+ 批处理工程仍可运行；5000套 broad simulations 文件完整；Codex可持续执行；服务器在 fresh pilot 前已完成 scaling benchmark；错误在当前阶段处理，不跨阶段带入。

科研性能由 fresh Real-SWAT+ 实验决定。时间表只描述可控工程工作量。

## 2. 阶段工期

| 阶段 | 主要工作 | 主动工作日 | 新增 Real-SWAT+ |
|---|---|---:|---:|
| R0 | DL4SWAT 数据审计、clean-room CNN复现 | 3–7 | 0 |
| R1 | South Branch数据契约、runner等价审计、4编码器点反演 | 5–10 | 20–80验算 |
| R2 | NPE/MAF或NSF、SBC/coverage/TARP/PPC | 5–10 | 0 |
| R3 | 受控misspecification与posterior trust冻结 | 3–7 | 0–100 |
| R4 | DDS/TuRBO/PISO集成、三seed fresh pilot | 5–9 + 0.5–2天计算 | 1782 |
| R5 | 五seed确认、消融、统计、locked validation | 7–14 | 最多4500（含可复用合规轨迹） |

### 里程碑时间

- **最快路径**：约3周得到初步 pilot，要求公开复现、数据适配和NPE均一次通过；
- **合理预期**：4–6周得到决定性 pilot；
- **保守区间**：7–8周，覆盖旧代码/数据格式和runner语义修复；
- **论文级正式结果**：从现在起约7–12周，包括五seed、消融、locked validation和完整图表。

以2026年9月2日为起点，合理预期的 pilot 窗口约为2026年9月30日至10月14日；正式结果窗口约为2026年10月21日至11月25日。

## 3. Real-SWAT+计算量

Pilot：

```text
3 methods × 3 seeds × 198 evaluations = 1782 runs
```

本机历史吞吐约454 runs/hour时，纯模拟理论下限约3.9小时。序贯批次、文件复制、代理重训、checkpoint、失败重试会提高wall-clock，工程预算按0.5–2天。

正式确认上限：

```text
3 methods × 5 seeds × 300 evaluations = 4500 runs
```

纯模拟理论下限约9.9小时。新服务器必须重新执行W4/W6/W8/W12/W16 scaling；本机W6结论不直接迁移。

## 4. GPU与内存

- 固定CNN/TCN/BiLSTM：12–24 GB GPU足够；
- Patch Transformer与NPE flow：建议24 GB；
- 5000 × 3 gauges × 约5114日的float32流量本体约0.29 GiB，显存主要由时序激活和后验网络决定；
- Real-SWAT+吞吐主要依赖CPU、RAM、NVMe和隔离工作目录。
