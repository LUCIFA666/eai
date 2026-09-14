# 仿真生成数据

目标：了解通过仿真环境自动化生成大规模训练数据的方法和代表性工具，作为真机数据的重要补充。

真机数据采集成本高、速度慢，仿真生成数据可以低成本大规模扩充训练集。核心思路是在仿真环境中通过程序化或策略引导的方式自动生成操作轨迹，再用于策略预训练或数据增强。仿真数据的主要挑战是 sim-to-real gap——仿真中有效的数据不一定能直接迁移到真机。

## [MimicGen](04-simulation-generated-datasets/01-mimicgen.md)

NVIDIA 等团队发布的自动化数据生成框架。给定少量人类示教轨迹，MimicGen 会把示教拆成 object-centric 子任务片段，再根据新场景中的物体位姿进行变换和执行。论文中从约 200 条人类示教生成了 18 个任务上的 50K+ demonstrations；仓库当前发布数据集为 12 个任务、48K+ demonstrations。

[https://github.com/NVlabs/mimicgen](https://github.com/NVlabs/mimicgen)

## [RoboCasa](04-simulation-generated-datasets/02-robocasa.md)

大规模家庭厨房仿真平台，基于 MuJoCo / robosuite 构建。RoboCasa365 当前提供 365 个日常任务、2500+ 厨房场景、3200+ 物体，以及人类遥操作和 MimicGen 合成示教数据，适合研究多任务家庭操作、场景泛化和仿真数据预训练。

[https://github.com/robocasa/robocasa](https://github.com/robocasa/robocasa)

## [DexMimicGen](04-simulation-generated-datasets/03-dexmimicgen.md)

MimicGen 思路在双臂和灵巧操作领域的扩展。DexMimicGen 面向 bimanual dexterous manipulation，从 60 条人类源示教出发，在 9 个任务、多种机器人形态和仿真环境中生成 20K+ demonstrations，适合研究双臂协调、灵巧手操作和 humanoid manipulation 的数据扩增。

[https://github.com/NVlabs/dexmimicgen](https://github.com/NVlabs/dexmimicgen)
