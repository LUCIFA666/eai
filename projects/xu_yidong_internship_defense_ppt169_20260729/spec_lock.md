<!-- ppt-master-schema: spec-lock/v1 -->
# Execution Lock

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## communication
- audience: 答辩评委、实习导师与实验室老师；具备机器人或机器学习背景，重点关注本人实际完成的工作、技术理解、工程严谨性与后续研究潜力。
- objective: 汇报预测式世界模型实习成果、复现证据与个人理解，并使评委认可本人继续开展具身智能与世界模型研究的能力和规划。
- core_message: 我不仅跑通了多条预测式世界模型复现链路，还形成了从论文理解、环境搭建、训练评测、问题定位到证据化交付的完整方法，并计划将其用于具身机器人中的预测、规划与控制闭环。
- consumption_mode: presentation

## mode
- mode: pyramid

## visual_style
- visual_style: ink-notes

## colors
- background: #F5F0E6
- secondary_bg: #E4DED2
- primary: #111111
- accent: #D94841
- secondary_accent: #2D5B8A
- body_text: #191919
- muted_text: #625E57
- grid: #C8C0B3
- positive: #2F7D5C

## typography
- font_family: SimSun, Georgia, serif
- title_family: DengXian, Impact, sans-serif
- body_family: SimSun, Georgia, serif
- data_family: DengXian, Consolas, monospace
- body: 32
- title: 56
- subtitle: 44
- lead: 38
- annotation: 24
- footnote: 18
- data: 72

## icons
- library: chunk-filled
- inventory: chunk-filled/book-open, chunk-filled/route, chunk-filled/chart-line, chunk-filled/code-block, chunk-filled/circle-checkmark, chunk-filled/lightbulb, chunk-filled/target-arrow, chunk-filled/robot

## images
- p04_plan: images/plan_montage.png | source=user | pattern=左侧大幅完整证据图，右侧用手绘括号连接指标与个人判断 | crop=no-crop
- p04_metrics: images/extended_metrics_curve.png | source=user | pattern=页面底部横向证据带，顶部保留三项结果与评估口径 | crop=no-crop
- p05_pipeline: images/reproduction-pipeline.png | source=user | pattern=右侧主图，左侧以三条手写批注说明本人完成的验证层级 | crop=no-crop
- p05_pusht: images/pusht_real_50_first_frame.png | source=user | pattern=作为 96% 成功率下方的横向结果条，与主流程图形成证据组合 | crop=no-crop
- p07_reconstruction: images/tokenizer_reconstruction.png | source=user | pattern=上半页横向无裁切证据带，旁注“重建不等于预测” | crop=no-crop
- p07_prediction: images/world_model_prediction.png | source=user | pattern=下半页横向无裁切证据带，旁注随机实体误差与分布解释 | crop=no-crop

## page_rhythm
- P01: anchor
- P02: anchor
- P03: anchor
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: anchor
- P09: breathing
- P10: dense
- P11: anchor
- P12: breathing

## pptx_structure
- mode: flat

## forbidden
- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`
- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters
