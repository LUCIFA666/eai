# 导航与场景数据集

目标：了解面向视觉语言导航和室内场景理解的数据集，支持移动机器人的空间推理和任务导航研究。

导航数据集与操作数据集关注的问题不同：操作数据关注"怎么抓/放/操作"，导航数据关注"去哪里、怎么走、怎么理解空间"。对于移动操作机器人而言，导航能力和操作能力同样重要。导航数据集通常基于真实室内 3D 扫描场景，结合自然语言指令，训练 agent 在未见过的环境中完成目标导航。

## [Matterport3D](06-navigation-scene-datasets/01-matterport3d.md)

大规模真实室内 RGB-D / 3D 场景数据集，包含 90 个建筑级场景、约 10,800 个全景视点和 194,400 张 RGB-D 图像，并提供 camera poses、textured meshes、floor plans、region annotations 和 object instance semantic annotations。它是 R2R、Matterport3DSimulator、Habitat 等导航和场景理解研究的重要场景底座。

[https://github.com/niessner/Matterport](https://github.com/niessner/Matterport)

## [Room-to-Room (R2R)](06-navigation-scene-datasets/02-room-to-room-r2r.md)

基于 Matterport3D 和 Matterport3DSimulator 构建的视觉语言导航基准。R2R 包含 7,189 条路径和 21,567 条人工自然语言指令，并提供 train / val-seen / val-unseen / test 划分和标准评测指标，用来测试 agent 能否根据路线描述在真实室内全景场景中导航到目标位置。

[https://github.com/peteanderson80/Matterport3DSimulator](https://github.com/peteanderson80/Matterport3DSimulator)
