# SimpleVLA-RL 文件索引：dataset

覆盖 `dataset` 分组，共 `5` 个 Python 文件。

| 文件 | 行数 | 架构作用 | 顶层类 | 顶层函数 | 主要导入 |
|---|---:|---|---|---|---|
| `verl/utils/dataset/__init__.py` | 17 | LIBERO/RoboTwin 数据索引和 dataloader；公共入口/工具 | - | - | rl_dataset, rm_dataset, sft_dataset |
| `verl/utils/dataset/rl_dataset.py` | 211 | LIBERO/RoboTwin 数据索引和 dataloader；数据读取/组织 | RLHFDataset, BufferedDataLoader | collate_fn | numpy, omegaconf, os, pandas, torch, transformers, typing, verl |
| `verl/utils/dataset/rm_dataset.py` | 143 | LIBERO/RoboTwin 数据索引和 dataloader；数据读取/组织 | RMDataset | download_files_distributed | os, pandas, torch, transformers, typing, verl |
| `verl/utils/dataset/rob_dataset.py` | 255 | LIBERO/RoboTwin 数据索引和 dataloader；数据读取/组织 | LIBERO_Dataset, Robotwin_Dataset, BufferedDataLoader | collate_fn | json, numpy, omegaconf, os, pandas, torch, transformers, typing |
| `verl/utils/dataset/sft_dataset.py` | 174 | LIBERO/RoboTwin 数据索引和 dataloader；数据读取/组织 | SFTDataset | - | pandas, torch, transformers, typing, verl |
