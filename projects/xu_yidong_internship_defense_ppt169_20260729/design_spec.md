<!-- ppt-master-schema: design-spec/v1 -->
# Xu Yidong Internship Defense - Design Spec

## I. Project Information

| Item | Value |
| --- | --- |
| Project Name | Xu Yidong Internship Defense |
| Canvas Format | PPT 16:9 (1280 × 720) |
| Page Count | 12 |
| Target Audience | 答辩评委、实习导师与实验室老师；具备机器人或机器学习背景，重点关注本人实际完成的工作、技术理解、工程严谨性与后续研究潜力。 |
| Communication Intent | 先汇报实习期间围绕预测式世界模型完成的学习、复现与证据交付，再用关键实验图和问题修复说明个人贡献与理解，最后说明如何把这些积累延伸到具身智能、VLA/WAM 与机器人规划控制研究。 |
| Desired Audience Outcome | 评委能够清楚区分本人完成的复现工作与论文原始贡献，理解每条复现链路的结果、边界和技术判断，并认可我继续开展具身智能与世界模型研究的能力和规划。 |
| Core Message / Ask / Action | 我不仅跑通了多条预测式世界模型复现链路，还形成了从论文理解、环境搭建、训练评测、问题定位到证据化交付的完整方法，并计划将其用于具身机器人中的预测、规划与控制闭环。 |
| Delivery Context | 主要用于有主讲的中文现场答辩，建议控制在约分钟；次要用于会后独立阅读与实习成果留档。 |
| Artifact Afterlife | 作为实习总结、后续夏令营或科研交流材料，并可复用为项目复盘与研究方向说明。 |
| Reading Mode | presentation |
| Content Strategy | 尽可能展现自己的独特理解 |
| Design Style | pyramid 结论先行叙事 + ink-notes 手绘批注视觉；纸张与印刷墨色方向 |
| Formula Policy | mixed |
| AI Image Acquisition Path | not applicable — provided assets only |
| Generation Mode | continuous |
| Spec Refinement | disabled |
| Speaker Notes | enabled — Stage 3 proactive policy |
| Custom Animations | disabled — Stage 3 proactive policy |
| Narration Audio | disabled — Stage 3 proactive policy |
| Created Date | 2026-07-29 |

## II. Canvas Specification

| Property | Value |
| --- | --- |
| Format | PPT 16:9 |
| Dimensions | 1280 × 720 |
| viewBox | `0 0 1280 720` |
| Margins | 40 px outer safe margin |
| Content Area | 1200 × 640 px within the safe margins |

## III. Visual Theme

### Theme Style

- **Mode**: pyramid
- **Visual style**: ink-notes
- **Theme**: 一份写在研究者白板上的复现实验答辩；证据图保持原貌，论点用手绘墨线、圈画、括号和批注组织。
- **Tone**: 严谨、坦诚、克制，但有鲜明的个人判断；强调“我做了什么、我如何判断、我准备继续做什么”。

### Color Scheme

| Role | HEX | Purpose |
| --- | --- | --- |
| Background | #F5F0E6 | 主纸张底色，承载大面积留白 |
| Secondary background | #E4DED2 | 局部证据衬底、图注带和轻量分区 |
| Primary | #111111 | 手绘墨线、主标题和结构骨架 |
| Accent | #D94841 | 关键结论、风险边界、圈画和强调 |
| Secondary accent | #2D5B8A | 方法、未来路径和正向技术标注 |
| Body text | #191919 | 正文与说明文字 |
| Muted text | #625E57 | 来源、脚注和次级说明 |
| Grid | #C8C0B3 | 淡化的手绘辅助线和图注分隔 |
| Positive | #2F7D5C | 已通过的验证关卡 |

## IV. Typography System

### Font Plan

| Role | Chinese | English | Fallback tail |
| --- | --- | --- | --- |
| Title | DengXian | Impact | sans-serif |
| Body | SimSun | Georgia | serif |
| Data | DengXian | Consolas | monospace |

- **Title stack**: DengXian, Impact, sans-serif
- **Body stack**: SimSun, Georgia, serif
- **Data stack**: DengXian, Consolas, monospace
- **Role rationale**: Data is a recurring role on reproduction-result, metric, command, and model-interface pages; the monospace Latin face keeps numbers and code-like labels scannable.

### Font Size Hierarchy

| Purpose | Anchor Size (px) |
| --- | ---: |
| Body | 32 |
| Title | 56 |
| Subtitle | 44 |
| Lead | 38 |
| Annotation | 24 |
| Footnote | 18 |
| Data / KPI | 72 |

## V. Layout Principles

### Page Structure

- **Header area**: 结论式页标题靠左；用一条略有起伏的手绘下划线或短括号落下主张，不使用机械直线标题栏。
- **Content area**: 一页只承载一个主张。证据页优先采用大图 + 少量批注；概念页采用手绘中心节点、分支箭头、圈画和跨栏括号。避免等权卡片网格。
- **Footer area**: 左侧记录材料来源或实验口径，右侧为页码；均使用 muted text，证据页不得遮挡图片标签。

### Spacing Specification

| Element | Current Project |
| --- | --- |
| Safe margin | 40 px |
| Content block gap | 28 px |
| Icon-text gap | 12 px |

## VI. Icon Usage Specification

- **Primary bundled library**: chunk-filled

| Purpose | Icon Path | Page |
| --- | --- | --- |
| 学习与材料梳理 | chunk-filled/book-open | P02, P03 |
| 技术路线与研究路径 | chunk-filled/route | P03, P11 |
| 评测指标与趋势 | chunk-filled/chart-line | P04, P08 |
| 代码、环境与工程链路 | chunk-filled/code-block | P02, P10 |
| 验证通过与证据闭环 | chunk-filled/circle-checkmark | P02, P06, P10 |
| 个人理解与方法判断 | chunk-filled/lightbulb | P07, P09 |
| 目标与未来方向 | chunk-filled/target-arrow | P11, P12 |
| 具身机器人系统 | chunk-filled/robot | P11 |

## VIII. Image Resource List

| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| plan_montage.png | 1152 × 984 | 1.17 | 展示 DINO-WM 规划迭代过程 | Experimental evidence | 左侧大幅完整证据图，右侧用手绘括号连接指标与个人判断 | no-crop | user | Existing | DINO-WM PointMaze planning montage；保留全部帧与标签 | embedded | local |
| extended_metrics_curve.png | 1961 × 747 | 2.63 | 展示 DINO-WM PushT / Wall 有界评估曲线 | Data chart | 页面底部横向证据带，顶部保留三项结果与评估口径 | no-crop | user | Existing | DINO-WM 50-eval metrics；保留坐标轴、图例和曲线 | embedded | local |
| reproduction-pipeline.png | 1672 × 941 | 1.78 | 展示 LeWM 从权重到训练与 MPC 的复现链路 | Process diagram | 右侧主图，左侧以三条手写批注说明本人完成的验证层级 | no-crop | user | Existing | LeWM reproduction pipeline；保持节点与箭头完整 | embedded | local |
| pusht_real_50_first_frame.png | 736 × 288 | 2.56 | 提供 LeWM 真实 Push-T 评测视觉证据 | Experimental evidence | 作为 96% 成功率下方的横向结果条，与主流程图形成证据组合 | no-crop | user | Existing | LeWM official-weight Push-T evaluation first frame | embedded | local |
| tokenizer_reconstruction.png | 1921 × 586 | 3.28 | 对比真实帧与 tokenizer 条件重建 | Experimental comparison | 上半页横向无裁切证据带，旁注“重建不等于预测” | no-crop | user | Existing | Δ-IRIS tokenizer conditional reconstruction | embedded | local |
| world_model_prediction.png | 1886 × 586 | 3.22 | 对比真实下一帧与 world-model 单步想象 | Experimental comparison | 下半页横向无裁切证据带，旁注随机实体误差与分布解释 | no-crop | user | Existing | Δ-IRIS one-step world-model imagination | embedded | local |

## IX. Content Outline

### Part 1: Conclusion and Work Map

#### Slide 01 - Cover

- **Audience move**: 从“不知道这段实习做了什么” → 立刻抓住主线：复现只是入口，形成研究判断和验证方法才是核心产出。
- **Layout**: 大面积留白；标题左上，右下用手绘箭头串起“论文 → 代码 → 指标 → 判断 → 机器人闭环”。底部小字写姓名、学校和答辩主题。
- **Title**: 从复现到研究：预测式世界模型实习答辩
- **Core message**: 我把多条世界模型路线转化为可运行、可验证、可解释的实验闭环。
- **Content**: 主标题；副标题“徐亦栋｜同济大学自动化”；醒目手写句“把论文跑通，不等于把问题想清楚”；小字标签“DINO-WM · LeWM · Δ-IRIS · TD-MPC2”。
- **Cover impact**: 以“论文 → 代码 → 指标 → 判断”的手绘演进链作为视觉钩子，最后一箭指向机器人闭环。
- **Motion suggestion**: 先出现主标题，再依次揭示五个链路节点，帮助观众建立整场答辩的认知骨架。

#### Slide 02 - Internship Outcome

- **Audience move**: 从“可能只是读论文、跑代码” → 理解实习产出覆盖知识、工程、结果和交付四个层次。
- **Layout**: 左侧一句大结论；右侧四个不规则手绘框，分别用图标标注“知识地图、复现链路、实验结果、证据交付”。底部嵌入个人背景小条。
- **Title**: 实习的核心产出，是一套可验证的世界模型复现方法
- **Core message**: 我完成的不只是若干运行记录，而是从理解到验证再到交付的完整方法。
- **Content**: 四项产出：①梳理预测式世界模型四条建模路线；②跑通 DINO-WM、LeWM、Δ-IRIS、TD-MPC2 等关键链路；③用成功率、训练进度、PSNR/MAE 和策略回报记录结果与边界；④整理固定提交、环境、脚本、日志、哈希与复现报告。个人背景条：“同济大学自动化｜GPA 4.83/5.00｜专业排名 1/69｜研究兴趣：具身智能、VLA/WAM、机器人系统”。
- **Visualization**: 四层成果堆叠，最上层“个人判断”跨越其余三层，强调知识、工程与研究能力的统一。
- **Native shape suggestion**: 用四个不规则手绘框围绕中心结论；框体保持 SVG 手绘路径，不采用机械卡片。

#### Slide 03 - Four Modeling Routes

- **Audience move**: 从“世界模型是一类相似方法” → 建立四条路线的统一比较框架。
- **Layout**: 中央写“任务相关的预测状态”，四条手绘分支分别连接像素/潜变量、视觉表征、离散 token、控制潜变量；每条分支带“预测对象—决策接口—代表方法”。
- **Title**: 四条路线的差异，归根结底是“预测什么、如何决策”
- **Core message**: 世界模型不一定重建像素；真正关键的是表示能否支持稳定预测与闭环决策。
- **Content**: ①从像素预测到潜变量想象：DreamerV3，latent imagination actor-critic；②视觉表征动态：DINO-WM / LeWM，feature prediction + goal matching；③Token 化动态：IRIS / Δ-IRIS，离散 token dynamics + actor-critic；④面向控制的潜变量：TD-MPC2，reward/value-aware latent model + MPPI。统一验收问题：“预测表示是否保留了对控制有用的信息？”。
- **Visualization**: 四分支概念地图；每条路线只保留一个对象、一个接口和一个代表方法，不堆论文列表。
- **Motion suggestion**: 按路线顺时针逐条揭示，最后出现中央统一问题。

### Part 2: Reproduction Evidence and Personal Understanding

#### Slide 04 - DINO-WM

- **Audience move**: 从“预训练视觉特征只是感知表征” → 理解其可以直接构成目标条件规划空间，并看到本人复现证据。
- **Layout**: 左侧放 plan_montage.png；右上写三项结果，右下写个人判断；底部横跨 extended_metrics_curve.png，所有图片保持完整。
- **Title**: DINO-WM：预训练视觉特征可以直接成为规划空间
- **Core message**: 在固定有界评估口径下，DINO-WM 的特征空间支持 PointMaze、PushT 与 Wall 的规划闭环。
- **Content**: 实测结果：“PointMaze success_rate = 1.0；PushT 43/50 = 86%，Wilson 95% CI [0.738, 0.930]；Wall 47/50 = 94%，Wilson 95% CI [0.838, 0.979]”。本人工作：“固定源码提交与 DINOv2 版本；修复 MuJoCo EGL 与运行兼容问题；封装运行与结果统计脚本；用 max_iter=5 构造可复跑的 50-eval 有界评估”。个人理解：“如果表征空间保持了可用于目标匹配的几何结构，就不必先还原每个像素再规划。”。
- **Images**: plan_montage.png + extended_metrics_curve.png；两图均为原始复现证据，no-crop。
- **Native-ready**: no
- **Motion suggestion**: 先显示规划拼图，再揭示三项结果，最后圈出“表征空间的几何可操作性”。

#### Slide 05 - LeWorldModel

- **Audience move**: 从“稳定 JEPA 需要复杂技巧” → 理解两项损失即可构成可用于 MPC 的紧凑预测模型，并看到完整验证层级。
- **Layout**: 左侧用大号“96%”和三条批注承载结论；右侧放 reproduction-pipeline.png；底部放 pusht_real_50_first_frame.png。
- **Title**: LeWM：更简洁的 JEPA 目标也能服务真实控制
- **Core message**: LeWM 用 prediction loss + SIGReg 避免表示坍塌，并在官方 Push-T 权重上完成 48/50 成功的 MPC 评测。
- **Content**: 结果：“50 episode，48/50 成功，成功率 96.0%，评测耗时 363.62 秒”。本人验证：“SHA-256 与 strict=True 权重加载；像素/动作编码和下一嵌入预测；MSE/SIGReg 有限且可反传；两套加载 API；MPC 候选 cost；两个训练 batch 与 checkpoint reload”。个人理解：“LeWM 的关键不是生成一张未来图，而是让预测嵌入与目标嵌入之间的距离能够成为规划代价。”。
- **Images**: reproduction-pipeline.png + pusht_real_50_first_frame.png；保持流程节点、画面和内嵌文字完整。
- **Motion suggestion**: 先落下 96% 结果，再沿流程图从权重验证走到 MPC，最后出现个人理解批注。

#### Slide 06 - Delta-IRIS Reproduction Boundary

- **Audience move**: 从“程序启动就算复现成功” → 接受分层验收，并能准确判断 Δ-IRIS 当前完成度。
- **Layout**: validation_matrix.png 居中放大；左上写结论，右侧用红色圈画论文性能层，用绿色标出前三层通过。
- **Title**: Δ-IRIS：复现必须分层，“跑通”不等于论文性能
- **Core message**: 环境、工程和预训练推理层已验证；scratch 长训尚未完成 5M 和正式评估，因此不能宣称论文最终分数已复现。
- **Content**: 四层标准：“环境层通过；工程层通过；预训练推理层通过；论文性能层未完成”。稳定长训快照：“epoch 27；360,006 dataset steps；2,032 episodes/segments；名义 5M 进度 7.20%”。本人判断：“复现结论必须与证据等级一一对应；官方 checkpoint 可证明推理链路，但不能替代从头训练结果。”。
- **Images**: validation_matrix.png，no-crop；图外批注不得覆盖矩阵文本。
- **Native-ready**: no
- **Motion suggestion**: 按四层从下到上逐项揭示，前三层加通过标记，最后停在未完成层并解释边界。

#### Slide 07 - Delta-IRIS Prediction Understanding

- **Audience move**: 从“图像看起来像就是预测好” → 区分条件重建、单步想象与随机未来分布。
- **Layout**: 上半页放 tokenizer_reconstruction.png，下半页放 world_model_prediction.png；右侧纵向手绘括号写三条判断。
- **Title**: Δ-IRIS：未来不是一张最好看的图，而是一组条件分布
- **Core message**: Tokenizer 重建验证压缩质量，world model 想象才验证条件预测；随机实体应通过分布而非单张样本解释。
- **Content**: 证据一：“Tokenizer 条件重建 MAE 0.00043786，PSNR 57.5892 dB；编码器看到了真实下一帧，因此不是未来预测”。证据二：“World model 单步想象 MAE 0.00358743，PSNR 30.4654 dB；生成时不输入真实下一帧”。个人理解：“误差集中在随机实体位置；同一历史与动作可采样不同 Δ-token，这不是失败，而是不确定性的建模对象。报告时应展示分布与典型误差，而不是只挑最好的一张。”。
- **Images**: tokenizer_reconstruction.png + world_model_prediction.png；上下两条均完整显示。
- **Motion suggestion**: 先显示重建并划掉“预测”标签，再显示单步想象，最后圈出“分布”。

#### Slide 08 - TD-MPC2

- **Audience move**: 从“世界模型越逼真越好” → 理解控制导向 latent、短期模型预测和长期价值估计的分工。
- **Layout**: 左侧手绘闭环“观测 → latent → 动作序列采样 → 短期 reward rollout + terminal Q → 执行第一步”；右侧三项复现证据与一条边界说明。
- **Title**: TD-MPC2：世界模型只需预测对控制有用的信息
- **Core message**: TD-MPC2 用任务导向 latent 预测支撑短期规划，再用 Q 函数补足有限 horizon 之外的价值。
- **Content**: 机制：“policy prior 提出动作；MPPI/CEM 在 latent 中采样并评估 512 条动作序列；预测 reward 累积并以 terminal Q bootstrap；只执行优化序列第一步”。复现证据：“官方 dog-run checkpoint 单 episode reward 762.2；154k 训练步时 reward 134.0，151k 最高 157.3；10k 仅证明训练链路可用，正式复现建议 7M 步并报告多 seed”。个人理解：“规模化的难点不只在动力学模型，而在 latent 稳定、reward/value 尺度、Q 过估计和多任务接口。”。
- **Visualization**: 手绘控制闭环 + 三个数据钉；不画未经来源支持的性能对比。
- **Motion suggestion**: 沿控制闭环依次揭示，terminal Q 在最后出现，用来解释为什么短 horizon 仍可做长期决策。

### Part 3: Synthesis, Method and Future Plan

#### Slide 09 - Three Cross-Project Judgments

- **Audience move**: 从“看到四个独立项目” → 记住三条可迁移的研究判断。
- **Layout**: 三个大号手写判断围绕中央问题“什么才是好的世界模型？”，用不规则箭头连接对应项目缩写。
- **Title**: 跨四条路线，我形成了三条统一判断
- **Core message**: 好的世界模型由任务相关表示、可校准的不确定性和闭环决策价值共同定义。
- **Content**: 判断一“表示不等于重建”：DINO-WM / LeWM 说明 feature geometry 可以直接支撑目标匹配与规划。判断二“预测不等于一张图”：Δ-IRIS 说明随机未来应报告分布、边界和误差位置。判断三“规划不等于长 rollout”：TD-MPC2 用短期模型预测 + terminal Q + policy prior 形成更可扩展的闭环。总结句：“评测最终要回到任务成功率、策略回报、稳定 rollout 与泛化，而不是只看视觉质量。”。
- **Visualization**: 中心问题 + 三分支判断；每个分支含一个代表项目和一个验收信号。
- **Motion suggestion**: 三条判断依次出现，最后中央问题被圈成“任务相关的可预测状态”。

#### Slide 10 - Reproducible Engineering Method

- **Audience move**: 从“复现是一次性运行” → 理解本人能够把实验转成可复跑、可审计、可交付的工程证据。
- **Layout**: 横向七步手绘链条；下方三类典型故障用“问题 → 修复 → 证据”呈现。
- **Title**: 可复现工程，把一次运行变成可追溯证据
- **Core message**: 固定版本、分层 smoke、严格加载、有界评估和证据打包，让实验结论可被复核。
- **Content**: 七步链条：“固定代码提交 → 隔离环境 → CUDA/EGL 探针 → 最小 smoke → checkpoint 严格加载 → 有界/正式评估 → 脚本、日志、哈希与图表交付”。典型修复：“DINOv2/Transformers 版本漂移；无显示器服务器的 MuJoCo EGL；Hydra launcher、nightly 依赖与下载超时；max_iter、step=0 与官方权重/从头训练等评测语义”。结果：“每个结论都能指向命令、日志、指标或落盘产物。”。
- **Visualization**: 七步证据链，最后一个节点为“可复核结论”。
- **Native shape suggestion**: 使用 stock block-arrow 语义的连续步骤，但以 ink-notes 手绘路径表达，不采用机械渐变箭头。
- **Motion suggestion**: 按复现顺序逐步揭示七个节点；每出现一个故障，就紧接着显示对应修复与证据。

#### Slide 11 - Future Plan

- **Audience move**: 从“复现经验停留在游戏/仿真任务” → 看见其如何迁移到具身机器人研究问题。
- **Layout**: 三条向前延伸的手绘路径汇聚到“预测—规划—控制闭环”；每条路径配一个图标和当前基础。
- **Title**: 下一步，把世界模型嵌入真实机器人决策闭环
- **Core message**: 我会围绕接触交互、VLA/WAM 与复杂动力学控制，研究任务相关预测状态如何提升闭环决策。
- **Content**: 路径一“人形机器人 HOI 模仿学习”：在 HDMI 复现和自定义数据接入基础上，继续研究接触几何、局部规划与交互稳定性。路径二“VLA / WAM 协同”：在 π0 / OpenPI 与 Flow Matching 实验基础上，让 VLA 提供动作先验，让世界模型进行 rollout、风险检查与重规划。路径三“复杂动力学 + MPC”：在无人机—悠悠球项目的残差动力学、潜空间世界模型和捕获概率预测基础上，完善旋转跟随、减摆与末端捕获闭环。统一问题：“如何学习既能泛化、又能被规划器真正使用的预测状态？”。
- **Visualization**: 三条研究路径 → 一个机器人闭环；路径之间不设置虚构时间或指标。
- **Motion suggestion**: 三条路径分别进入中心闭环，最后显示统一研究问题。

#### Slide 12 - Closing

- **Audience move**: 从“了解项目细节” → 形成对个人研究能力与发展方向的明确判断。
- **Layout**: 左侧大号结论，右侧三条手写能力标签；底部用一支向前的红色箭头连接“复现者 → 问题定义者 → 系统验证者”。
- **Title**: 目标不是重复更多论文，而是定义问题并完成验证闭环
- **Core message**: 我希望继续做能被运行、被验证、被解释，并最终进入机器人闭环的具身智能研究。
- **Content**: 三条能力：“快速进入新方向：从论文到代码结构”；“严谨完成验证：区分 smoke、官方权重与从头训练”；“形成个人判断：把表示、预测与控制放在同一闭环中”。收束句：“从复现出发，走向任务相关世界模型与具身系统研究。”。
- **Closing impact**: 以“复现者 → 问题定义者 → 系统验证者”的转变作为最后记忆点，不使用空洞的感谢页。
- **Motion suggestion**: 最后只保留转变箭头和收束句，形成答辩结束的视觉停顿。

## X. Speaker Notes Requirements

- **Generation**: enabled
- **Filename**: match each SVG filename under `notes/`
- **Content**: 每页先说结论，再解释图像证据、本人完成的工作、结果边界和个人理解；定量内容逐项对应项目 `sources/` 中的复现报告，不把论文原始贡献表述为本人贡献。证据页补充评估口径与“官方权重/从头训练/smoke”区别，未来规划页明确为个人研究方向。
- **Total duration**: approximately 12 minutes
- **Notes style**: formal but conversational, conclusion-driven, technically precise
- **Presentation purpose**: report internship work, demonstrate research understanding and engineering rigor, and articulate future research direction
