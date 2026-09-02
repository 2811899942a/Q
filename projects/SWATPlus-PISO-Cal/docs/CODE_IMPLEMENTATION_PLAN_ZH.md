# 代码实现计划

## 1. 模块边界

```text
src/swatplus_piso/
├── data.py                 数据契约、训练期 scaler
├── metrics.py              NSE/KGE/PBIAS/RMSE与三站聚合
├── models/
│   ├── encoders.py         CNN/TCN/BiLSTM/Patch Transformer
│   ├── point_inverse.py    确定性参数反演
│   └── posterior.py        sbi NPE接口
├── calibration/
│   ├── ood.py              模拟域偏移诊断
│   ├── proposal.py         posterior/prior候选混合与多样性
│   └── sequential.py       通用序贯评价循环
└── swat/
    └── runner.py           隔离工作目录Real-SWAT+执行器
```

## 2. 下一步必须补齐的生产代码

### 2.1 Public reproduction adapter

- 读取 `swat_params_sobol_1000realz.csv`；
- 读取 `flow_wy_sobol_1000realz.csv`；
- 读取官方 train/val/test indices；
- 只在800个训练 realization 上拟合参数和流量 scaler；
- 输出统一 `theta.npy/qsim.npy/qobs.npy`；
- 写出源文件 MD5、数组形状和日期 manifest。

### 2.2 South Branch adapter

复用现有正式 SWAT+ 写参和 `channel_sd_day`/目标输出解析逻辑，封装成：

```python
parameter_writer(workdir, theta)
output_parser(workdir) -> qsim[gauge, time]
```

必须用同一正式候选执行：旧工作流与新 runner 输出逐日完全一致，指标完全一致，才允许接入优化器。

### 2.3 Deterministic training

需要实现：

- realization-level split；
- DataLoader；
- train-only scaler；
- bounded normalized parameters；
- early stopping；
- checkpoint与config hash；
- 三seed汇总；
- 参数写回后的 Real-SWAT+ 验证。

### 2.4 SBI training

- 使用 `sbi==0.27.0`；
- 只向NPE提供 `(theta, qsim)`；
- 自定义多站时序 embedding；
- MAF与NSF；
- posterior保存与重载；
- SBC、expected coverage、TARP、posterior predictive check；
- 真实Qobs只用于条件化和后续 Real-SWAT+评分。

### 2.5 Online optimizers

所有DDS/TuRBO/PISO共用：

- 同一参数边界；
- 同一目标函数；
- 同一初始42点；
- 同一 evaluation accountant；
- 同一 W6 runner；
- 每个候选原子级checkpoint；
- 失败重试和重复候选去重；
- 可断点续跑。

## 3. 代码质量门

```text
A. compile/import PASS
B. pytest PASS
C. toy smoke PASS
D. public data manifest PASS
E. one-candidate old/new runner equivalence PASS
F. same formal scheduled/remote execution context dry-run PASS
G. all methods evaluation accounting PASS
```

E–G完成以前，不得宣称真实实验框架已部署。
