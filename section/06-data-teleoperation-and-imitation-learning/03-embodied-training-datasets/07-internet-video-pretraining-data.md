# 互联网视频预训练数据

目标：了解互联网视频和众包短视频如何用于具身智能模型的视觉、动作语义和视频-语言预训练。

互联网视频和众包短视频（YouTube 教学视频、日常活动视频、短动作表演视频等）是具身 AI 预训练的重要数据源。虽然这类视频通常没有机器人动作标注，但包含丰富的物体交互、操作步骤和因果关系信息。通过自监督、动作分类或视频-语言对比学习，模型可以先学到通用视觉表征和动作语义，再微调到机器人任务上。

## [Something-Something V2](07-internet-video-pretraining-data/01-something-something-v2.md)

面向时序动作理解的短视频数据集，包含 220,847 条众包视频、174 个动作标签和 318,572 条物体文本标注。它用模板化语言描述人手与日常物体的动作关系，强调动作方向、起止状态和是否完成动作，适合用来训练视频模型的时序理解能力，但不能直接当作机器人控制轨迹。

[https://www.qualcomm.com/developer/software/something-something-v-2-dataset](https://www.qualcomm.com/developer/software/something-something-v-2-dataset)

## [HowTo100M](07-internet-video-pretraining-data/02-howto100m.md)

从 YouTube 教学视频中自动构建的大规模视频-文本弱监督语料，包含约 1.22M 个带旁白教学视频、约 136M 个视频片段，覆盖超过 23K 个视觉任务。它用 ASR narration 作为文本监督，适合训练 text-video embedding 和视频-语言预训练模型，但不能直接当作机器人动作轨迹。

[https://github.com/antoine77340/howto100m](https://github.com/antoine77340/howto100m)
