# A流域硬锁文件

本文是本项目的最高优先级研究区约束。后续对话、Codex、脚本和实验计划若与本文冲突，以本文为准。

## 唯一正式研究区

**South Branch Potomac A basin**。

正式模型：现有 SWAT+ rev.62 工程。禁止为了复现论文而重建或替换正式流域。

三站固定：

| USGS | SWAT+ channel |
|---|---:|
| 01605500 | 12 |
| 01606000 | 17 |
| 01606500 | 18 |

时间固定：

- 2000–2002 warm-up/context；
- 2003–2016 development；
- 2017–2020 locked validation；
- 2021–2024 final test。

参数维度固定为现有正式 14D。参数名称、上下界、absolute/relative/replacement 写入语义必须从现有 A 流域正式 runner 审计继承，PISO 项目不得自行重新定义。

正式目标函数同样从现有 A 流域正式 calibration workflow 原样继承，在 A0 形成 hash/文本快照后冻结。

## 论文的唯一角色

Mudunuru/DL4SWAT 等论文用于：

1. 提供深度学习参数反演的已发表方法母体；
2. 帮助确定数据预处理、encoder、inverse mapping 和 baseline 设计；
3. 可选 public-data clean-room reproduction，用于 implementation sanity check。

论文流域不是研究区；论文数据不能混入 A 流域正式训练；论文预训练权重默认不得迁移到 A 流域。

## A流域已有资产

下一对话必须优先扫描 `D:/SWAT+_3V3/A_SouthBranchPotomac/`，定位当前正式工程、runner、14D 字典、观测数据和 archive。

已知历史信息用于定位，不允许替代本地文件核验：

- SWAT+ rev.62；
- 三站 ch12/ch17/ch18；
- 历史 archive 约7400条，其中约5000条是 broad pool，约2400条来自 DeepCal/DDS/DE/BO 等目标导向轨迹；
- broad pool 历史最大 mean NSE 约0.496；目标导向轨迹包含更高质量点，因此两层数据必须隔离；
- DeepCal 真实USGS结果约0.506，DDS同预算约0.557；pseudo-target 曾约0.92，说明 simulation-to-observation gap 必须显式处理；
- 当前机器 Real-SWAT 历史 scaling：W6 约453.98 runs/hour，为稳定优选；换机器必须重测 scaling。

以上数值在正式使用前由本地文件重新核验。
