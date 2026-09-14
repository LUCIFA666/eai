# 机器人自动与半自动采集

本组讲不靠人实时操控、由机器人自动或半自动产生数据的方式。全自动(脚本/规划器/自监督)用人力少、动作一致,适合规整任务与 bootstrapping;半自动(策略 rollout + 人工修正)能采到模型真实会遇到的 OOD 与失败恢复数据。仿真生成数据(MimicGen 类)见第 6 章仿真生成数据。

## 本组页面

| 四级页面 | 重点 |
|---|---|
| [脚本、规划器与自监督采集](04-robot-autonomous-collection/01-scripted-planner-selfsup.md) | 全自动生成成功/失败轨迹 |
| [Policy Rollout + 人工修正](04-robot-autonomous-collection/02-policy-rollout-correction.md) | 半自动,采 OOD 与失败恢复数据 |
