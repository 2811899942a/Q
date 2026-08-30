# DSSAT M15 13.5/13.8 冻结分享版

Branch: `release/dssat-m15-13p5-13p8-v1`

本目录用于分享 2026-08-30 已冻结的 DSSAT 4.8.5 M15-13.5 / M15-13.8 五件套。后续继续优化温度精度的研究不得覆盖本目录或改写本分支中的冻结材料。

## 冻结配置

- M15-13.5: DTRc = 13.5 C, alpha = 6.407985379809223，项目主方案。
- M15-13.8: DTRc = 13.8 C, alpha = 6.749813473189908，稳健性/敏感性方案。
- 上游最终下边界审查 run: `33259349242`。
- 冻结依据 commit: `ef34289f50d889e15de9df1d0a0323c21b36f20c`。
- 项目部署决策 commit: `07ec04abb355f46f76c5a70be1d025ad5ae8ad18`。

## 原始五件套 SHA256

以下哈希对应 ChatGPT 生成并完成 QA 的原始文件，内容不得改写：

- `DSSAT_M15_Xinjiang_13p5_13p8_Package_v1.zip`
  - `ba21810ca9b98454f3af35b42cf8061586f41c36655d7e8e780d98fbe94d06e5`
- `DSSAT_M15_13p5_13p8_科研详细教程.docx`
  - `d20376cb5c576e78518b19d65db09dafc7b323a0ab416b8bf6e39b491e7df39d`
- `DSSAT_M15_新疆区域普适性与可迁移性验证报告.docx`
  - `300838be9c3e54455b29df879fb2b91f6157bef5241a9ee0cc83554f38331cc0`
- `DSSAT_M15_优化模型数据清单.xlsx`
  - `fe152d39268da9995971f8de1e445957f38f3d8cf25d4a0ddd52b7b3ee18930d`
- ZIP 内部 `PACKAGE_AUDIT.txt` 与 `MANIFEST_SHA256.txt` 共同构成第5项审计/完整性材料。

## GitHub 内可直接浏览材料

- `科研详细教程.md`: 与冻结 DOCX 对应的纯文本科研教程。
- `新疆区域普适性与可迁移性验证报告.md`: 与冻结 DOCX 对应的纯文本报告。
- `PACKAGE_AUDIT.txt`: 软件包 QA 记录。
- `MANIFEST_SHA256.txt`: 软件包内部逐文件 SHA256。
- 原始算法、验证脚本和最终审查结果仍保存在同一仓库 `research/dssat_dtr/` 下，并由上述冻结 commits 锁定。

## 重要规则

本分支只用于分享冻结成果。任何“继续提升逐小时温度精度”的新实验必须另开研究分支，并保持 13.5/13.8 当前版本作为不可变基准。温度新方案先按温度观测独立评估，再向 CERES-Maize 传播验证产量、物候、ET 与水分胁迫响应。
