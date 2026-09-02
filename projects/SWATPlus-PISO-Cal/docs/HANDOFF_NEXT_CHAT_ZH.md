# 下一对话执行交接

## 固定身份

下一对话负责本项目的 Codex 指令、代码审查、运行结果核验和 Gate 判定。不得重新扩大到 V3B、跨流域、CMIP6、PLUS 或新的强耦合架构。

## 仓库位置

当前可写 GitHub 连接器没有“新建仓库”动作，因此项目以完全独立目录写入：

```text
2811899942a/Q/projects/SWATPlus-PISO-Cal
```

目录自带 `pyproject.toml`、许可证、代码、测试、配置和决策 Gate，可以原样迁移为独立仓库。

## 首个任务

1. 克隆/拉取项目；
2. 建立 Python 3.11 环境；
3. 安装 `.[dev,sbi]`；
4. 运行 `pytest -q` 与 `python scripts/run_toy_smoke.py`；
5. 阅读 `DATA_PROVENANCE_AND_FAIRNESS_ZH.md`，先隔离 broad 与 observed-directed archive；
6. 下载 DL4SWAT Zenodo 数据并记录 MD5；
7. 输出数据文件树、数组形状和日期范围；
8. 将数据转换为统一 data contract；
9. 只实现并复现 deterministic CNN；
10. 复现报告通过 Gate R0 后，才迁移 South Branch。

## 禁止事项

- 不复制 DL4SWAT GitHub 中无许可证的源代码；
- 不把真实 observed NSE 伪装成 SNPE 标签；
- 不提前读取 2017-2020 或 2021-2024；
- 不以单个 seed 宣称胜出；
- 不把 5000 离线运行当作零成本；
- 不增加参数维度；
- 不增添模型动物园；
- 不用 archive replay 替代 fresh Real-SWAT+ benchmark。

## 第一份 Codex 指令应包含

```text
TASK = R0_PUBLIC_DL4SWAT_CLEANROOM_REPRODUCTION

INPUT:
- Zenodo 10.5281/zenodo.7271945
- expected Data.zip md5 d9547cebe2a6607dec5355a45296d5bd
- clean-room project code only

OUTPUT:
- manifest.json
- file_tree.txt
- data_contract conversion
- train/val/test shape audit
- scaler fit audit
- deterministic CNN training
- synthetic parameter metrics
- observed-parameter inference
- reproducibility report

STOP:
- no South Branch changes
- no SBI
- no fresh Real-SWAT+
```

## Gate reporting template

```text
STAGE=
STATUS=PASS|FAIL|BLOCKED
DATA_HASH_OK=
LEAKAGE_AUDIT=
PRIMARY_METRICS=
DEVIATIONS_FROM_PAPER=
CAUSES=
NEXT_ALLOWED_ACTION=
```
