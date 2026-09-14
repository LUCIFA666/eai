# 人类先演示再迁移

本组讲不直接操控机器人、而是先采人类示教再 retarget 到机器人的方式。优点是机器人可不在采集现场、场景多样性强;代价是采到的不是机器人真实 joint action,存在 embodiment 与动力学 gap,迁移到真机的注意见本章 Sim2Real。这些方法的数据集与迁移在第 6 章已系统讲(ego 数据集、UMI、人形全身数据、人体视频迁移),本组从真机采集/落地视角串一遍。

## 本组页面

| 四级页面 | 重点 |
|---|---|
| [UMI 手持夹爪](03-human-demo-transfer/01-umi-handheld.md) | 手持夹爪 + 相机,in-the-wild 采集 |
| [人体视频与第一视角数据](03-human-demo-transfer/02-human-video-egocentric.md) | ego/互联网视频作人类示教 |
| [手部 Mocap](03-human-demo-transfer/03-hand-mocap.md) | 便携手部动捕,迁移到灵巧手 |
| [外骨骼与数据手套](03-human-demo-transfer/04-exoskeleton-gloves.md) | 手指级动作 + 接触反馈 |
