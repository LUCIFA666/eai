# Habitat 中的常见数据集：Matterport3D、Gibson、HM3D、Replica

目标：理解 Habitat 常用室内场景数据集的差异，知道 Matterport3D、Gibson、HM3D、Replica 和 ReplicaCAD 分别适合什么任务，以及使用时要检查哪些文件和许可。

Habitat 里的数据集不是“贴图背景”。它决定了智能体进入什么世界：房间是不是完整，语义标注有没有，对象能不能交互，训练和测试场景怎么划分。很多实验结果的差异，表面上看是算法差异，实际上也可能来自数据集和 split 差异。

## 先分清两类数据

Habitat 里至少有两类数据。

第一类是 **scene dataset**。它提供 3D 场景，比如一栋房子的 mesh、语义文件、navmesh 和 scene config。

第二类是 **episode dataset**。它提供任务实例，比如 PointNav 的起点和目标点，ObjectNav 的目标类别和起点，ImageNav 的目标图像。

```text
scene dataset: 提供房间和建筑
  -> episode dataset: 在这些房间里采样任务
  -> Habitat-Lab task: 读取 episode 并定义成功条件
```

只下载 scene dataset，不代表你已经有了 ObjectNav episode；只有 episode 文件，没有对应 scene，也跑不起来。

## 常见场景数据集对比

| 数据集 | 类型 | Habitat 中常见用途 | 注意点 |
|---|---|---|---|
| Matterport3D | 真实建筑级 RGB-D 扫描 | 早期导航、VLN、EQA、跨场景泛化 | 数据访问和下载有许可要求，格式和脚本较老 |
| Gibson | 真实室内重建 | 视觉导航、跨数据集评估 | 语义信息通常需要额外资源，版本要写清楚 |
| HM3D | Habitat-Matterport 3D，大规模建筑级重建 | 现代 PointNav、ObjectNav、语义导航 | 访问需要官方流程，semantic 文件和 config 要对应 |
| Replica | 高质量室内重建 | 高质量渲染、导航、室内视觉实验 | 规模不是最大，但视觉质量高 |
| ReplicaCAD | 可交互 CAD 公寓场景 | Habitat 2.0、Rearrangement、Home Assistant Benchmark | 重点是可交互物体和关节对象，不是普通静态场景 |

## Matterport3D

Matterport3D 是早期室内视觉导航和语言导航工作中非常重要的数据来源。它来自真实室内空间的 RGB-D 扫描，包含建筑级场景、相机位姿、表面重建和语义标注。

在 Habitat 生态里，Matterport3D 常用于 PointNav、VLN、EQA 等任务。它的优势是场景真实、空间尺度大、相关历史工作多；限制是数据访问、格式转换和许可边界都要认真处理。

## Gibson

Gibson 也常用于视觉导航。它提供真实空间重建，适合做跨场景泛化实验，比如训练在一个数据集上，测试在另一个数据集上。

使用 Gibson 时要注意语义信息。不是所有 Gibson 使用场景都天然带有你需要的语义标注。如果任务是 PointNav，只需要几何和可导航区域；如果任务是 ObjectNav，就要看是否有可用的对象语义或配套资源。

## HM3D

HM3D 的全称是 Habitat-Matterport 3D。它是 Habitat 生态里很重要的现代场景数据集，论文中给出的规模是 1000 个建筑级 3D 重建场景，并强调其可导航空间、视觉质量和场景多样性。

HM3D 常和现代 Habitat 导航任务放在一起使用，尤其是 HM3D-Semantics 和 ObjectNav 相关工作。相比只看 RGB 的导航，ObjectNav 更依赖语义标注，因此你要确认 `.semantic.glb`、`.semantic.txt` 和 `scene_dataset_config.json` 是否齐全。

一个典型 HM3D 目录可能需要同时有：

```text
hm3d_basis.scene_dataset_config.json
hm3d_annotated_basis.scene_dataset_config.json
train/
val/
minival/
  scene_id/
    xxx.basis.glb
    xxx.basis.navmesh
    xxx.semantic.glb
    xxx.semantic.txt
```

不同下载 uid 和版本会影响实际文件结构，所以正式实验要按官方说明核对。

## Replica 和 ReplicaCAD

Replica 是高质量室内场景重建数据集。它很适合展示高质量渲染和室内视觉任务，但场景规模不是最大。

ReplicaCAD 则是 Habitat 2.0 里非常关键的数据。它不是简单的真实扫描，而是 artist-authored、annotated、reconfigurable 的公寓场景，包含可交互对象和关节物体，例如柜门、抽屉等。正因为有这些交互元素，Habitat 2.0 才能做 Rearrangement 和 Home Assistant Benchmark。

简单说：Replica 更偏高质量静态室内场景；ReplicaCAD 更偏可交互家庭环境。

## 使用数据集前的检查清单

| 检查项 | 为什么重要 |
|---|---|
| 数据许可 | 有些数据需要申请，不能随意再分发 |
| scene config | Habitat-Sim 需要它来正确加载数据集中的资源 |
| navmesh | PointNav / ObjectNav 依赖可导航区域 |
| semantic 文件 | ObjectNav、semantic sensor 依赖语义标注 |
| episode 文件 | 任务实例不等于场景本身 |
| split | 训练和评测不能混在一起 |
| 版本 | 不同数据版本可能导致指标不可比 |

## 本页小结

Habitat 的数据集决定实验边界。Matterport3D 和 Gibson 是早期导航工作常用真实场景，HM3D 是 Habitat 生态里重要的大规模现代场景，Replica 视觉质量高，ReplicaCAD 则支撑 Habitat 2.0 的交互和重排任务。写实验时一定要同时记录 scene dataset 和 episode dataset。

## 导航

- 上一页：[Habitat-Lab](03-habitat-lab.md)
- 返回：[Habitat 简介](../01-habitat-simulation.md)
- 下一页：[典型任务](05-typical-tasks.md)

## 进一步阅读可以看：

- [Habitat-Sim supported datasets](https://github.com/facebookresearch/habitat-sim/blob/main/DATASETS.md)
- [HM3D dataset](https://aihabitat.org/datasets/hm3d/)
- [ReplicaCAD dataset](https://aihabitat.org/datasets/replica_cad/)
- [Matterport3D paper](https://arxiv.org/abs/1709.06158)