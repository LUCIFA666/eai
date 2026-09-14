# 人-物交互数据集

目标：了解专注于手部与物体精细交互的数据集，为灵巧操作和 affordance 研究提供数据支持。

人-物交互（Hand-Object Interaction, HOI）数据集记录人类手部与物体之间的接触、抓取和操作过程，通常包含手部姿态、物体 6DoF 位姿、接触区域和交互力等信息。这类数据与通用操作视频不同，精度更高、标注更密，是灵巧手策略、抓取规划和 affordance 建模的重要训练来源。

## HOI4D

大规模 4D 人-物交互数据集，使用 RGB-D 传感器采集，提供逐帧的手部姿态、物体位姿、动作分割和接触标注。涵盖 800+ 个物体实例和多种日常交互类别，支持 4D 场景理解和交互预测研究。

[https://github.com/leolyliu/HOI4D-Instructions](https://github.com/leolyliu/HOI4D-Instructions)

## [DexYCB](03-hand-object-interaction-datasets/01-dexycb.md)

NVIDIA 发布的灵巧手抓取数据集，记录人手抓取 YCB 物体集中 20 种常见物体的过程。提供多视角 RGB-D 图像、手部关节标注和物体 6DoF 位姿，适合手部姿态估计和抓取策略研究。

[https://github.com/NVlabs/dex-ycb-toolkit](https://github.com/NVlabs/dex-ycb-toolkit)

## [OakInk](03-hand-object-interaction-datasets/02-oakink.md)

上海交通大学等团队发布的手-物交互数据集，强调交互意图（intent）和 affordance。不仅记录手抓取物体的姿态，还标注了交互意图和物体功能区域，使研究者可以建模"为什么这样抓"而非仅"怎样抓"。

[https://github.com/oakink/OakInk](https://github.com/oakink/OakInk)
