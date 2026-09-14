# Project Genie 与世界创作

## 本页目标

Genie 3 是底层世界模型，Project Genie 是面向用户的实验性原型。

本页重点介绍：

```text
Project Genie 与 Genie 3 的关系
World Sketching 如何创建世界
用户如何探索和 Remix 世界
环境和角色 Prompt 分别控制什么
Street View Grounding 增加了什么
产品功能与研究模型能力有什么区别
```

## 模型与产品原型

需要区分：

```text
Genie 3：
根据世界描述、历史和动作生成下一世界状态

Project Genie：
将 Genie 3 封装成可创建、探索和 Remix 世界的网页原型
```

Project Genie 还结合：

```text
Nano Banana Pro：
生成和修改 World Sketch

Gemini：
支持语言和产品交互

Street View：
提供部分现实地点图像起点
```

## 三个核心流程

Project Genie 官方将主要体验分为：

```text
World Sketching
World Exploration
World Remixing
```

它们对应：

```text
定义世界
-> 进入并探索
-> 基于已有世界重新创作
```

## World Sketching

<video src="./assets/project-genie-world-sketching.mp4" controls width="100%"></video>


该视频来自 Google Project Genie 官方演示，展示用户如何通过文字、生成图或上传图像定义环境、角色和视角，并在进入世界前修改 World Sketch。该过程决定初始视觉状态，但不会预先生成完整地图。

## Environment Prompt

环境 Prompt 主要描述：

```text
场景类型
地面和道路
天气与时间
视觉风格
建筑和关键对象
环境中的动态效果
```

详细 Prompt 可以提高方向控制，但不能保证每个细节都严格执行。

## Character Prompt

角色 Prompt 描述：

```text
受控主体是什么
主体外观
移动方式
动作范围
运动产生的视觉效果
```

角色可以是：

```text
人
动物
机器人
车辆
飞行器
幻想生物
普通物体
```

移动方式可以是行走、驾驶、飞行、游泳或滑行。

## World Sketch 的作用

World Sketch 确定：

```text
第一帧
角色初始外观
局部环境
视角
视觉风格
```

它不是完整三维地图。

用户离开初始画面后，后续区域仍由世界模型生成。

## World Exploration

<video src="./assets/project-genie-exploration.mp4" controls width="100%"></video>

该视频来自 Project Genie 官方演示，展示用户进入 World Sketch 后如何移动角色、调整相机并探索新区域。需要观察新路径是否实时产生、角色控制是否连贯，以及环境能否在探索中保持一致。该案例不能证明所有用户世界都具有相同控制稳定性。

## World Remixing

World Remixing 允许用户基于已有世界修改：

```text
环境风格
角色类型
移动方式
地形
视角
Prompt 内容
```

Remix 是生成式重新解释，不是传统游戏编辑器中的精确资产修改。

## 导出内容

Project Genie 可以让用户下载探索视频。

下载结果是视觉记录，不是：

```text
三维模型
游戏项目源码
地图文件
碰撞体
物理状态
导航网格
```

## Street View Grounding

Project Genie 后续加入 Street View Grounding。

用户可以选择现实地点，再添加创意风格和角色。

例如：

```text
现实桥梁
+ 海底风格
-> 水下幻想环境

现实历史街区
+ 黑白电影风格
-> 重新想象的历史世界
```

Street View 提供现实图像锚点，但后续世界仍由生成模型扩展。

## Grounding 不等于真实地图

生成世界仍可能：

```text
改变道路结构
遗漏建筑
生成不存在的对象
改变空间尺度
错误延伸遮挡区域
```

因此，它不能作为：

```text
精确地图
导航工具
工程测量
数字孪生
安全关键模拟
```

## 产品限制与模型能力

Project Genie 是实验性原型。

初始官方说明包括：

```text
世界可能不完全写实
结果可能不严格遵循 Prompt
角色控制可能不稳定
控制可能有较高延迟
生成时长受到产品限制
```

产品版本限制不能直接等同于底层 Genie 3 模型的全部能力。

## 本页小结

Project Genie 将 Genie 3 组织成面向用户的世界创作流程。

World Sketching 用于定义环境和角色，World Exploration 让用户进入世界，World Remixing 支持重新创作。Street View Grounding 为世界加入现实地点图像起点，但生成结果仍不是精确现实地图。
