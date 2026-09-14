# Something-Something V2

目标：理解 Something-Something V2 为什么适合训练视频模型的时序动作理解能力，能分清 video clip、template label、object annotation、train / validation / test split 这些概念，也能判断它对具身 AI 有什么帮助、不能直接替代哪些机器人数据。

> 先修：动作识别、视频预训练、基本数据集 split 概念
> 建议：这一节重点看“模型为什么必须看动作过程”，不要把 Something-Something V2 当成普通物体分类视频集
> 数据集规模：Something-Something V2 包含 220,847 个短视频片段，覆盖 174 类细粒度人类动作，完整视频数据约 19.4 GB。

Something-Something V2 是一个面向时序动作理解的视频数据集。它的特点很鲜明：视频通常只拍一个人用手和日常物体做一个短动作，标签不是“杯子”“桌子”这类物体类别，而是“把某物放到某物上”“把某物从某物上拿开”“假装把某物倒进某物里”这类动作模板。

这类数据对具身 AI 有价值，是因为机器人也需要理解动作过程。比如“把杯子放到桌上”和“从桌上拿起杯子”可能出现在同一张桌子、同一个杯子、同一只手的画面里，如果只看单帧图像，很容易混淆；必须看时间顺序，才能知道动作到底发生了什么。

一句话概括 Something-Something V2：

```text
Something-Something V2 收集 220,847 条众包短视频，
覆盖 174 个动作标签，
用模板化语言描述人手与日常物体之间的时序动作，
主要用于训练和评测模型是否真的理解视频里的动作过程。
```

## 它解决的是什么问题

很多视频数据集可以靠静态外观猜标签。比如画面里有篮球场，大概率是打篮球；画面里有钢琴，大概率是弹钢琴。这种数据当然有用，但它不一定逼着模型理解“动作如何随时间变化”。

Something-Something V2 刻意把问题设计得更难：物体本身不重要，动作关系才重要。同一个杯子、书、盒子、手机，可以出现在很多不同动作里：

```text
Putting something on top of something
Taking something out of something
Moving something up
Moving something down
Pretending to put something into something
Pushing something so that it falls off the table
```

这些标签里的 `something` 是占位符。数据集中真正的样本会把占位符填成具体物体，但模型最终要学的是动作语义，而不是记住某个物体类别。

这就非常接近具身智能里的一个基本问题：机器人不能只识别“这里有杯子”，还要理解“杯子正在被拿起、放下、推开、倒入、移近或移远”。

## 它到底包含什么

Qualcomm 的数据页面给出的 V2 口径如下：

| 项目 | 数量或形式 | 怎么理解 |
|---|---|---|
| video clips | 220,847 条 | 每条是一个短动作视频 |
| action labels | 174 类 | 模板化动作类别，不是物体类别 |
| object annotations | 318,572 条 | 填入模板占位符的物体文本 |
| train | 168,913 条 | 有标签训练集 |
| validation | 24,777 条 | 有标签验证集 |
| test | 27,157 条 | 下载包中的 test 样本不带标签 |
| video format | VP9 webm，12 FPS，高度 240 px | 适合批量视频训练的压缩格式 |
| download size | 约 19.4 GB | 视频压缩后仍然需要一定磁盘空间 |

这里最容易误解的是 `object annotations`。它不是 2D bounding box，也不是 segmentation mask，而是模板里 `[something]` 对应的文字物体描述。比如模板是：

```text
Putting [something] onto [something]
```

某条样本的占位符可能是：

```text
["a cup", "a table"]
```

这样它就能被读成“把一个杯子放到一张桌子上”。但训练动作分类时，标签通常还是模板级动作类别，而不是每个具体物体组合都变成一个新类别。

## 一条样本应该怎么看

用教程里的方式理解，一条 Something-Something V2 样本可以拆成四层：

```text
video clip
  ├─ frames: 一段几秒级短视频
  ├─ template: 动作模板，例如 Putting [something] onto [something]
  ├─ placeholders: 具体物体文本，例如 a cup / a table
  └─ label: 去掉具体物体后的动作类别
```

这里的重点不是“视频里出现了什么物体”，而是“物体之间发生了什么变化”。例如下面两个动作只看某一帧可能很像，但语义完全不同：

| 动作 | 关键区别 |
|---|---|
| Putting something onto something | 物体最后被放到另一个物体上 |
| Taking something off something | 物体一开始在上面，后来被拿走 |
| Moving something closer to something | 两个物体之间距离变小 |
| Moving something away from something | 两个物体之间距离变大 |
| Pretending to put something into something | 有动作意图，但没有真的完成放入 |

这就是 Something-Something V2 的价值：它让模型不能偷懒，只靠场景背景或物体外观猜答案。模型需要看手的运动、物体的位置变化、接触关系和动作结束状态。

## 为什么说它强调时序理解

以“把某物放到某物上”和“从某物上拿起某物”为例，单帧图像里都可能出现手、杯子和桌面。区别在于时间：

```text
Putting:
  cup in hand -> cup moves down -> cup rests on table -> hand leaves

Taking:
  cup on table -> hand approaches -> hand grasps cup -> cup leaves table
```

这两段的起点、终点和中间运动方向都不同。真正有用的视频模型要能把这些变化连起来，而不是只看最后一帧。

对具身 AI 来说，这种能力很重要。机器人执行任务时也要判断动作阶段：物体是不是已经接触桌面，手是不是松开，容器是不是被倾斜，目标物是不是从里面被取出。如果视觉模型能从 Something-Something V2 里学到这类时序关系，再迁移到机器人数据上，通常比只用静态图像预训练更接近操作任务需要的表征。

## 它和机器人数据有什么关系

Something-Something V2 不是机器人数据集。它没有机械臂关节角、末端执行器位姿、夹爪开合、力传感器、reward，也没有任务成功标注。它提供的是人类手-物交互视频和动作语义标签。

所以它适合做这些事：

| 用法 | 为什么合适 |
|---|---|
| 视频动作识别 | 标签就是动作类别 |
| 视频编码器预训练 | 逼迫模型学习时序变化，而不是只看物体外观 |
| 手-物交互语义学习 | 很多动作都围绕手和日常物体展开 |
| VLA / robot policy 的视觉前端预训练 | 可以提供“动作过程”相关的视觉先验 |
| affordance 相关预训练 | 模型能看到物体被推、放、拿、倒、移动时的变化 |

它不适合直接做这些事：

```text
不能直接训练机器人控制策略。
不能当作 imitation learning 的 action 轨迹。
不能提供机械臂动作空间。
不能评估真实机器人任务成功率。
不能替代真机遥操作数据。
```

更合理的用法是：先用 Something-Something V2 训练或评估视频表征，再把这个表征接到真实机器人数据上微调。例如先训练一个能区分“put / take / push / move / pretend”的视频 backbone，再在 LeRobot、Open X 或自采集机器人轨迹中学习具体动作输出。

## 它和 HowTo100M 有什么区别

同样放在“互联网视频预训练数据”这一组里，Something-Something V2 和 HowTo100M 的气质很不一样。

| 数据集 | 数据来源 | 标注方式 | 适合学什么 |
|---|---|---|---|
| Something-Something V2 | 众包拍摄的短动作视频 | 人工模板化动作标签 | 精细时序动作、手-物关系 |
| HowTo100M | YouTube 教学视频 | ASR 旁白和视频弱对齐 | 大规模视频-语言关联、任务步骤知识 |

Something-Something V2 更干净、更短、更像动作分类基准；HowTo100M 更大、更噪、更像视频-语言预训练语料。一个强调“动作到底是什么”，另一个强调“人类教程里讲了什么、做了什么”。

如果你要测试模型是否真正理解短动作过程，Something-Something V2 更合适；如果你要做大规模视频-语言预训练，HowTo100M 的规模优势更明显。

## 下载和使用时要注意什么

数据页面提供了视频和标注文件下载。视频是 VP9 编码的 webm 文件，帧率为 12 FPS，高度为 240 px。完整视频下载约 19.4 GB，通常会被拆成多个压缩包。

使用时要注意几件事。

第一，test split 没有标签。它用于提交评测或做无标签测试，不能当成本地监督训练集。

第二，object annotation 不是检测框。它只是模板占位符对应的文字，不要把它当成像素级或框级物体标注。

第三，动作类别之间有细微差别。有些类别差在方向，有些差在是否完成动作，有些差在接触关系。训练和分析错误样本时，最好看完整视频，不要只截一张图。

第四，视频是人类表演数据。它可以帮助模型学习人手和物体的时序关系，但迁移到机器人时还会遇到本体差异：人的手和机械夹爪不同，人的动作速度和机器人控制频率不同，摄像机视角也可能不同。

## 一个最小训练任务可以怎么设

如果只是想把它作为视频模型入门数据，可以从最简单的动作分类开始：

```text
输入：一段 video clip 的若干帧
输出：174 个动作类别中的一个
损失：cross entropy
评估：top-1 / top-5 accuracy
```

如果目标更接近具身 AI，可以把问题换成更有迁移意义的形式：

```text
输入：动作开始后的前半段视频
输出：预测动作类别或动作是否会完成
关注点：模型能否在动作还没结束时推断物体关系的未来变化
```

这比普通“看完整视频分类”更接近机器人场景。真实机器人不能等人把动作做完再反应，它需要在动作早期就判断对方可能要放下、拿起、推开还是倒入。

## 常见误解

**误解一：Something-Something V2 是机器人操作数据集。**

不是。它是人类手-物交互视频数据集，没有机器人状态和动作控制量。

**误解二：object annotations 是物体检测标注。**

不对。这里的 object annotations 是填进动作模板的文字物体描述，不是 bounding box，也不是 segmentation mask。

**误解三：只看单帧就能解决这个数据集。**

通常不行。很多类别的关键差异在动作方向、起止状态和是否完成动作，必须利用时间信息。

**误解四：它和 HowTo100M 是同一种数据。**

不是。Something-Something V2 是相对干净的短动作分类数据，HowTo100M 是大规模教学视频和 ASR 文本弱对齐数据。

**误解五：视频预训练好了，就可以直接控制机器人。**

不可以。视频预训练只能提供视觉和动作语义表征。机器人控制还需要真实或仿真的 action 数据、状态对齐、控制频率和任务成功信号。

## 小结

Something-Something V2 是“短视频时序动作理解基准”。它的价值不在规模最大，也不在提供机器人轨迹，而在于用 220,847 条短视频和 174 个模板化动作标签，逼迫模型理解物体关系如何随时间变化。对具身 AI 来说，它补的是视觉前端和动作语义预训练这一环；真正训练机器人策略时，还必须回到有状态、有动作、有任务边界的机器人数据集。

进一步阅读可以看：
- [Qualcomm 数据页面](https://www.qualcomm.com/developer/software/something-something-v-2-dataset)
- [The "Something Something" Video Database for Learning and Evaluating Visual Common Sense](https://arxiv.org/abs/1706.04261)