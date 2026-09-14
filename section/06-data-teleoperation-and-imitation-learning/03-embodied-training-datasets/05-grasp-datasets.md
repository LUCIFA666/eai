# 抓取专用数据集

目标：了解专门面向抓取位姿估计和灵巧操作的数据集，覆盖平行夹爪和多指灵巧手两类场景。

抓取是机器人操作最基础也最关键的能力。抓取专用数据集与通用操作数据不同，重点在于提供大量抓取位姿标注（grasp pose annotation），包括抓取点、抓取方向、抓取宽度和抓取质量评分等。这些数据直接服务于抓取检测网络和抓取规划算法的训练。

## [GraspNet-1Billion](05-grasp-datasets/01-graspnet-1billion.md)

上海交通大学 MVIG 团队发布的大规模平行夹爪抓取 benchmark。它包含 190 个真实杂乱场景、97,280 张 RGB-D 图像、88 个物体和 1.1B+ 6DoF grasp labels，并提供 seen / similar / novel 评测协议和 baseline，是通用物体抓取检测研究中的经典基准。

[https://github.com/graspnet/graspnet-baseline](https://github.com/graspnet/graspnet-baseline)

## [DexGraspNet](05-grasp-datasets/02-dexgraspnet.md)

北京大学、北京通用人工智能研究院、清华大学等团队发布的灵巧手抓取数据集。DexGraspNet 为 5355 个物体生成 1.32M 个 ShadowHand 抓取姿态，覆盖 133+ 个物体类别，并用 Isaac Gym 验证，适合研究多指灵巧手抓取合成和手-物体接触建模。

[https://github.com/PKU-EPIC/DexGraspNet](https://github.com/PKU-EPIC/DexGraspNet)
