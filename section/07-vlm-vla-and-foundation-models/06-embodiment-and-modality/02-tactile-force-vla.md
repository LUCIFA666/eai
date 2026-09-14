# 7.6.2 触觉与力觉 VLA

难度：**[中级]** | 预计用时：30 分钟  
先修：[视觉动作语言基础](../01-behavior-cloning/01-basic-formulation.md) → [第 3 章触觉传感硬件](../)

> 纯视觉 VLA 看不见"打滑""形变""挤压力"——这些都是接触密集任务（插拔、装配、擦拭）的核心信息。触觉和力觉为什么重要？因为机器人操作世界时，**接触就在指尖**。把触觉/力觉融入 VLA，本质上是给模型多开了一个感知维度，让它真正"摸"着做事情。本节讲清楚触觉 token 化、编码器选择、数据对齐，以及力反馈在接触密集任务中的实际增益。

## 学习目标

读完本页后，你应该能：

- 解释纯视觉 VLA 在接触密集任务上的核心瓶颈：为什么视觉看不见打滑和力？
- 对比不同触觉编码器设计：图像式触觉（GelSight/DIGIT）和 1D 力传感器分别怎么 token 化？
- 说清楚多模态融合位置放在哪里：早期融合（输入级）vs 后期融合（ backbone 中交叉注意力）各有什么优劣？
- 列出三类主要的视触语言对齐数据来源，以及每种来源的成本和质量。
- 用表格对比视觉-only VLA 和触觉 VLA 在不同任务上的成功率差异。

## 一、为什么 VLA 需要触觉/力觉？

### 纯视觉 VLA 的三个盲区

在大多数桌面抓取任务中，纯视觉已经够用。但一旦进入**接触密集型操作**，三个问题就出来了：

| 问题 | 纯视觉表现 | 触觉/力觉能提供什么 | 典型任务 |
|------|-----------|-------------------|---------|
| **打滑与形变不可见** | 物体已经在夹爪里打滑，视觉看不到接触力变化 | 指尖直接测量接触力和滑移，毫秒级响应 | 拧螺丝、插拔插头 |
| **装配对齐依赖力反馈** | 插销孔位偏差 1mm 视觉看不出来，但插不进去 | 力信号告诉你偏差方向，方便实时调整 | 轴孔装配、螺纹拧紧 |
| **擦拭按压需要恒力** | 擦玻璃时压多压轻视觉难判断 | 力传感器直接闭环，保持恒力 | 擦拭、抛光、打磨 |

> **初学者提示**：你可以闭着眼睛把钥匙插进锁孔——靠的就是指尖的触觉反馈。纯视觉 VLA 就像闭着眼睛找锁孔，只能瞎碰；加上触觉 VLA 就像睁开了"指尖的眼睛"，能一边摸一边调整。

### 触觉 VLA 的核心思路

> **把触觉传感器（或力传感器）的信号作为额外模态，和视觉、语言一起送入 VLA backbone，让模型在预测动作时直接利用触觉线索。**

### 和纯视觉 VLA 的对比

| 维度 | 纯视觉 VLA | 触觉 VLA（含力觉） |
|------|-----------|------------------|
| 观测维度 | 视觉 + 语言 + 本体关节 | 视觉 + 语言 + 触觉/力 + 本体关节 |
| 典型任务 | 可见物体抓取放置 | 接触密集型操作（装配、擦拭、拧动） |
| 数据需求 | 需要视-语-动对齐数据 | 需要视-触-语-动四元对齐数据 |
| 推理延迟 | 低 | 略高（增加一个编码器） |
| 传感器成本 | 低（只需相机） | 中（需要指尖传感器，价格几百到几千） |

## 二、触觉/力信号如何 token 化？

触觉传感器主要分两类，对应的 token 化方式完全不同。

### 2.1 图像式触觉：GelSight / DIGIT

这类传感器**把触觉转换成图像**——硅胶形变被相机拍成 2D 图像，然后用视觉编码器提取特征。

| 步骤 | 做法 |
|------|------|
| 1. 采集 | 触觉接触面形变 → 相机拍摄 → 得到 H×W×3 触觉图像 |
| 2. 编码 | 用预训练视觉 backbone（ResNet 或 SigLIP 变体）提取特征 |
| 3. token 化 | 特征图铺平成 sequence of tokens，和视觉 tokens 拼在一起 |

典型维度：
- 输入触觉图像：`[1, 3, 64, 64]`
- 特征输出：`[1, 1, 256]`（全局池化后）或 `[1, 16, 256]`（不池化）

伪代码：

```python
import torch
import torch.nn as nn
import torchvision.models as models

# GelSight/DIGIT 触觉图像编码器
class TactileImageEncoder(nn.Module):
    def __init__(self, output_dim: int = 256):
        super().__init__()
        backbone = models.resnet18(pretrained=True)
        self.backbone = nn.Sequential(*list(backbone.children())[:-1])
        self.proj = nn.Linear(512, output_dim)

    def forward(self, tactile_images: torch.Tensor) -> torch.Tensor:
        """tactile_images: [B, 3, H, W]"""
        feats = self.backbone(tactile_images).squeeze()  # [B, 512]
        return self.proj(feats).unsqueeze(1)  # [B, 1, output_dim] -> 一个 tactile token

# 融合到 VLA
def forward_vla(image_tokens, lang_embed, tactile_images, action):
    tactile_tokens = tactile_encoder(tactile_images)  # [B, 1, D]
    all_tokens = torch.cat([image_tokens, tactile_tokens], dim=1)
    return backbone(all_tokens, lang_embed, action)
```

### 2.2 一维力/力矩传感器：FT 传感器

腕部力传感器（Force-Torque, FT）输出 6 维力/力矩向量：`[Fx, Fy, Fz, Mx, My, Mz]`，是低维向量。

token 化方式更简单：

| 做法 | 说明 |
|------|------|
| 归一化 | 将 6 维力力矩归一化到 [-1, 1] |
| 投影 | 线性投影到和视觉 token 相同维度 D |
| 加入序列 | 作为一个 token 和视觉 tokens 拼接 |

对比：

| 传感器类型 | 维度 | 编码器 | token 数量 per step |
|-----------|:---:|--------|-------------------|
| 图像式触觉（单指） | 64×64×3 | ResNet/SigLIP | 1~16 |
| FT 力传感器 | 6 | MLP | 1 |
| 多指触觉（五指） | 5×64×64×3 | 共享编码器 | 5~80 |

> **工程技巧**：触觉通常比视觉采样频率高（100~1000Hz vs 30~60Hz）。工程上常用时空压缩（3D 卷积或 VAE）把多个高频率触觉帧压缩成一个 token，和视觉时间对齐。

## 三、多模态融合架构：早融合 vs 晚融合

把触觉特征加到 VLA 里，有两种常见融合位置：

### 3.1 早期融合（输入级）

触觉特征在输入层就和视觉特征拼接，一起进 backbone：

```
图像 → 视觉编码器 → image tokens
触觉 → 触觉编码器 → tactile tokens
语言 → 文本编码器 → lang embedding
↓ 拼接 tokens
Transformer backbone
↓
输出动作
```

优点：
- backbone 可以在 early 层学习跨模态注意力
- 实现简单，不需要改 backbone 结构

缺点：
- 如果触觉缺失（推理时传感器掉了），模型直接罢工

### 3.2 后期融合（backbone 中交叉注意力）

触觉作为条件，通过交叉注意力注入到 backbone：

```
图像 → 视觉 tokens → backbone → KV
触觉 → 触觉 tokens → Q 投影 → 交叉注意力 → 更新特征
↓
输出动作
```

更进阶的设计是**不对称注意力**（Tactile-WAM）：只让触觉 token 参与关键层的注意力计算，避免浪费计算量。

### 对比

| 融合方式 | 实现难度 | 建模能力 | 鲁棒性（传感器掉了） |
|---------|:-------:|:--------:|:-------------------:|
| 早期融合 | 容易 | 中等 | 差 |
| 后期融合 | 中等 | 强 | 较好 |

> **当前主流**：大多数触觉 VLA 还是用早期融合——实现最简单，性能不差。Tactile-WAM 这类进阶工作才会用不对称后期融合。

## 四、视-触-语言对齐数据从哪来？

触觉 VLA 最头疼的问题是**数据采集**——你需要同时得到视觉、触觉、语言、动作四路对齐的数据。主要有三类来源：

| 数据来源 | 获取方式 | 成本 | 质量 | 代表性工作 |
|---------|---------|------|------|-----------|
| 遥操作采集 | 人带力反馈手套遥操作，同时记录四路信号 | 高（人工 + 遥操作设备） | 高（真实机器人） | Tactile-VLA, OmniVTA |
| 仿真生成 | 在仿真器给虚拟灵巧手加上虚拟触觉，自动生成大量数据 | 低（无硬件） | 中（有 sim2real gap） | Tactile Simulation Benchmark |
| 离线数据集 | 公开已采集的视触觉对齐数据集 | 极低 | 中，需要自己对齐语言 | YCB-Tactile, OmniTact |

典型接触密集型任务套件：
- peg insertion（轴孔插入）
- nut threading（螺母拧螺丝）
- gear meshing（齿轮啮合）
- bulb insertion（灯泡安装）
- power plug insertion（插头插入）

## 五、性能增益在哪里？

大量实验一致显示：触觉/力觉对接触密集任务有显著增益，但对普通抓取任务增益不大。

| 任务类型 | 视觉-only VLA 成功率 | 触觉 VLA 成功率 | 增益 |
|---------|-------------------|-----------------|------|
| 普通可见物体抓取 | 70~80% | 72~83% | +2~3% |
| 轴孔装配（偏差 1mm） | ~30% | ~65% | **+35%** |
| 螺纹拧紧 | ~25% | ~60% | **+35%** |
| 复杂曲面擦拭 | 不稳定，力波动大 | 稳定恒力控制 | 定性增益 |

> **关键结论**：触觉不是"万金油"——它只在**接触密集、力敏感**的任务上提供巨大增益。对于"看见目标→抓起来放下"这种纯视觉任务，加触觉意义不大。

## 六、代表性工作对比

| 工作 | 触觉类型 | 融合方式 | 核心思想 |
|------|---------|---------|---------|
| Tactile-VLA (2025) | 图像式触觉 | 早期融合 | 第一个完整的视触语言动作 VLA |
| Tactile-WAM (2025) | 触觉 + FT | 不对称后期融合 | 把触觉加入世界动作模型，预测未来触觉 |
| OmniVTA (2025) | 多模态触觉 | 3D 卷积时空压缩 | 视触觉联合世界建模 |
| VTLA (2025) | 戴盟视触觉传感器 | 早期融合 | 首个国产商用传感器+VLA 架构 |

## 七、阅读卡片

```yaml
tactile_force_vla_reading_card:
  核心问题: 纯视觉 VLA 在接触密集任务上看不见什么？如何用触觉/力觉补全？
  核心答案: 把触觉/力信号编码成 token 和视觉语言拼接，让模型在接触密集任务上利用力反馈

  触觉传感器分类:
    - image_tactile: GelSight / DIGIT，输出 2D 图像，用视觉编码器
    - ft_sensor: 腕部六维力力矩，输出 6 维向量，用 MLP 投影

  tokenization:
    - image_tactile: ResNet/SigLIP → 全局池化 → 1 个 token
    - ft_force: 归一化 → 线性投影 → 1 个 token
    - multi_finger: 每个手指共享编码器，多个 tokens

  fusion_architectures:
    early_fusion: 输入层拼接 tokens → 一起进 backbone，实现简单
    late_fusion: 交叉注意力注入，建模灵活，性能略好
    asymmetric_attention: 只在关键层让触觉参与，节省计算

  data_sources:
    teleoperation: 人工遥操作，成本高质量好
    simulation: 仿真自动生成，成本低有 sim2real gap
    public_datasets: 离线公开数据，成本最低

  performance_gain:
    - ordinary_grasping: +2~3%（边际增益）
    - contact_rich_tasks: +20~35%（大幅增益）
    - typical_tasks: 轴孔装配、螺纹拧紧、擦拭、插头插入

  key_insight: 接触就在指尖——纯视觉看不见的力，让指尖直接告诉模型

  challenges:
    - 四路对齐数据采集成本高
    - 传感器价格比普通相机贵
    - 不同机器人传感器位置不同，迁移难
    - 触觉采样频率比视觉高，需要时间对齐
```

## 八、自测问题

1. 为什么纯视觉 VLA 在轴孔装配任务上表现差？1mm 的孔位偏差视觉能分辨吗？触觉为什么能分辨？
2. GelSight/DIGIT 这类图像式触觉和六维 FT 力传感器在 token 化上有什么区别？各适用于什么场景？
3. 早期融合和后期融合各有什么优缺点？如果做一个研究原型，你会选哪个？为什么？
4. 如果训练时每个手指都有触觉传感器，但推理时一个传感器坏了，mask 机制如何处理？能不能让模型鲁棒？
5. 为什么触觉在普通抓取任务上增益不大，在接触密集任务上增益很大？这和任务的信息需求有什么关系？

---

Sources:
- [Tactile-VLA: Unlocking Vision-Language-Action with Touch (2025)](https://blog.csdn.net/YMWM_/article/details/157870095)
- [Tactile-WAM: Touch-Aware World Action Model](http://m.toutiao.com/group/7656691906709979654)
- [OmniVTA: Omnidirectional Visual-Tactile World Modeling for Contact-rich Manipulation](https://blog.csdn.net/yorkhunter/article/details/159508937)
- [VTLA: Vision-Tactile-Language-Action Architecture (DaiMeng Robotics)](http://m.toutiao.com/group/7646132889662259747)
- [GelSight](https://www.gelsight.com/)
- [DIGIT Tactile Sensor](https://digit.ml/)