# 论文导读与追踪入口

目标：知道具身智能论文从哪里出现、平时如何追踪新论文，以及如何借助会议、期刊、预印本、Awesome 列表和项目页筛选值得深入阅读的工作。

> 论文导读不只是“找论文链接”。对具身智能来说，一篇论文是否值得读，通常取决于它是否说清楚任务协议、机器人本体、数据来源、评测指标、代码与数据开放情况，以及是否有真实系统证据。

<p align="center">
  <a href="https://arxiv.org/list/cs.RO/recent"><img src="https://cdn.simpleicons.org/arxiv/B31B1B" width="34" alt="arXiv logo"></a>
  &nbsp;&nbsp;
  <a href="https://openreview.net/"><img src="https://openreview.net/favicon.ico" width="34" alt="OpenReview logo"></a>
  &nbsp;&nbsp;
  <a href="https://roboticsconference.org/"><img src="https://www.google.com/s2/favicons?domain=roboticsconference.org&sz=64" width="34" alt="RSS logo"></a>
  &nbsp;&nbsp;
  <a href="https://openaccess.thecvf.com/"><img src="https://openaccess.thecvf.com/favicon.ico" width="34" alt="CVF logo"></a>
  &nbsp;&nbsp;
  <a href="https://dblp.org/"><img src="https://dblp.org/img/favicon.ico" width="34" alt="DBLP logo"></a>
  &nbsp;&nbsp;
  <a href="https://www.semanticscholar.org/"><img src="https://www.semanticscholar.org/favicon.ico" width="34" alt="Semantic Scholar logo"></a>
  &nbsp;&nbsp;
  <a href="https://github.com/topics/embodied-ai"><img src="https://cdn.simpleicons.org/github/181717" width="34" alt="GitHub logo"></a>
  &nbsp;&nbsp;
  <a href="https://huggingface.co/lerobot"><img src="https://huggingface.co/front/assets/huggingface_logo-noborder.svg" width="34" alt="Hugging Face logo"></a>
</p>

## 学习目标

读完 12.1 后，你应该能：

- 区分正式发表、预印本、开放评审、论文集、项目页和社区列表的作用。
- 为“操作、导航、人形、VLA、世界模型、仿真评测”建立不同的论文追踪入口。
- 用一张阅读卡片记录论文版本、任务协议、机器人本体、数据、评测、开放资源和风险。
- 判断一篇论文适合“快速扫读、进入周报、深读复现、暂时观望”中的哪一类。

## 一、论文追踪流水线

```mermaid
flowchart LR
  A["发现线索<br>会议目录 / arXiv / OpenReview / Awesome"] --> B["确认版本<br>正式论文 / arXiv vN / OpenReview / 项目页"]
  B --> C["读任务<br>环境、本体、动作接口、数据来源"]
  C --> D["查证据<br>benchmark、真机视频、消融、失败案例"]
  D --> E["查资源<br>code、data、checkpoint、license、issue"]
  E --> F["决定动作<br>扫读 / 周报 / 深读 / 复现"]
```

图 12.1.1 论文追踪不是单点搜索，而是从线索到证据的闭环。越靠近“复现”，越要离开二手列表，回到论文、项目页、代码和数据本身。

## 二、入口地图

| 入口 | 代表资源 | 主要解决什么问题 | 阅读动作 |
|---|---|---|---|
| 正式会议与期刊 | RSS、CoRL、ICRA、IROS、TRO、IJRR、RA-L、Science Robotics | 判断工作是否通过同行评审，了解机器人系统、算法和实验的正式版本 | 查录用版本、补充材料、视频和引用格式 |
| 预印本 | arXiv `cs.RO`、`cs.CV`、`cs.LG`、`cs.AI` | 第一时间发现 VLA、world model、robot learning、多模态具身新工作 | 记录版本号、日期、是否已有正式录用和代码 |
| 开放评审 | OpenReview | 看评审意见、作者回复、实验争议和版本变化 | 重点读 reviewer 对实验协议、baseline 和边界的质疑 |
| 论文集与数据库 | IEEE Xplore、PMLR、CVF、ACL Anthology、DBLP、Semantic Scholar | 查正式版本、引用关系、作者谱系和相关工作网络 | 用数据库确认版本，用引用网络扩展阅读 |
| Awesome 与论文列表 | RoboScholar、Awesome LLM Robotics、Awesome RL-VLA、Awesome Humanoid Robot Learning | 快速按方向扫论文和项目线索 | 当方向索引用，不当事实来源 |
| 项目页与代码 | Project page、GitHub、Hugging Face、leaderboard | 查代码、模型、数据、demo、评测协议和复现说明 | 优先看 release、license、issue、数据卡和运行命令 |
| 补充线索 | 实验室博客、公司技术博客、newsletter、年度回顾 | 理解背景、作者解释和行业动向 | 只作为发现入口，不替代论文原文 |

## 三、五类常用资源卡片

<table>
  <tr>
    <td width="20%" align="center" valign="top">
      <a href="https://arxiv.org/list/cs.RO/recent"><img src="https://cdn.simpleicons.org/arxiv/B31B1B" width="36" alt="arXiv logo"></a><br>
      <strong>预印本</strong><br>
      <sub>每天扫新工作，记录版本和代码状态</sub>
    </td>
    <td width="20%" align="center" valign="top">
      <a href="https://openreview.net/"><img src="https://openreview.net/favicon.ico" width="36" alt="OpenReview logo"></a><br>
      <strong>开放评审</strong><br>
      <sub>看争议、边界、作者回复和最终版本</sub>
    </td>
    <td width="20%" align="center" valign="top">
      <a href="https://roboticsconference.org/"><img src="https://www.google.com/s2/favicons?domain=roboticsconference.org&sz=64" width="36" alt="RSS logo"></a><br>
      <strong>正式论文集</strong><br>
      <sub>确认录用版本、补充材料和引用格式</sub>
    </td>
    <td width="20%" align="center" valign="top">
      <a href="https://github.com/topics/embodied-ai"><img src="https://cdn.simpleicons.org/github/181717" width="36" alt="GitHub logo"></a><br>
      <strong>代码与列表</strong><br>
      <sub>查项目状态、issue、release 和社区索引</sub>
    </td>
    <td width="20%" align="center" valign="top">
      <a href="https://huggingface.co/papers"><img src="https://huggingface.co/front/assets/huggingface_logo-noborder.svg" width="36" alt="Hugging Face logo"></a><br>
      <strong>模型与数据</strong><br>
      <sub>查 model card、dataset card、Space 和每日论文</sub>
    </td>
  </tr>
</table>

## 四、细分章节

| 页面 | 内容 |
|---|---|
| [论文来源与入口地图](01-paper-reading-and-tracking/01-paper-sources-and-entry-map.md) | 会议期刊、预印本、评审平台、论文集、项目主页和社区索引的分工 |
| [会议、期刊](01-paper-reading-and-tracking/02-conferences-journals-and-proceedings.md) | 机器人、机器学习、视觉、NLP、多模态方向的正式发表入口 |
| [Awesome 论文集合与专题索引](01-paper-reading-and-tracking/03-awesome-lists-and-topic-indexes.md) | Embodied AI、LLM Robotics、RL-VLA、人形机器人等社区维护列表，以及博客、newsletter、年度回顾等补充线索 |

## 五、最小阅读卡片

```yaml
paper_reading_card:
  title: ""
  version:
    venue: "arXiv / RSS / CoRL / ICRA / IROS / NeurIPS / ..."
    date: ""
    url: ""
  task:
    problem: "manipulation / navigation / humanoid / VLA / world model / benchmark"
    embodiment: "single arm / dual arm / mobile robot / humanoid / dexterous hand"
    environment: "real / sim / mixed"
  evidence:
    metrics: []
    baselines: []
    real_robot: false
    failure_cases: false
  resources:
    project_page: ""
    code: ""
    data: ""
    checkpoint: ""
    license: ""
  decision:
    action: "scan / weekly-report / deep-read / reproduce / wait"
    reason: ""
```

这张卡片的重点不是填满，而是防止只凭标题、机构和视频 demo 判断论文价值。具身智能论文如果缺少任务协议、机器人本体和复现入口，很难进入工程路线。

## 六、真实追踪示例：π0.5 / openpi

下面用 Physical Intelligence 的 π0.5 作为示例。它适合展示一个常见情况：论文、博客和开源仓库都能找到，但“可以深读”和“可以在本课程复现”仍然是两件事。

| 入口 | 核验动作 | 本课程记录 |
|---|---|---|
| 官方博客 | 查作者如何解释 open-world generalization、真实场景和任务类型 | 用作动机和趋势入口，不直接当作实验协议 |
| arXiv 论文 | 查模型结构、任务、本体、数据来源、实验设置和限制 | 用作论文导读和方法分析入口 |
| openpi 仓库 | 查安装方式、模型类型、推理/微调示例、显存要求、license 和 issue | 用作工程参考；复现前还要确认权重、数据、硬件和任务配置 |
| 后续资源 | 查模型卡、数据卡、release、第三方复现或 benchmark | 决定是否从 deep-read 升级为 reproduce |

```yaml
paper_reading_card:
  title: "π0.5: a Vision-Language-Action Model with Open-World Generalization"
  version:
    arxiv: "https://arxiv.org/abs/2504.16054"
    official_blog: "https://www.pi.website/blog/pi05"
    openreview: "not found; do not treat as peer-review evidence"
  task:
    problem: "VLA / generalist robot policy / open-world manipulation"
    embodiment: "mobile manipulator and heterogeneous robot data in the official description"
    environment: "real-world manipulation plus mixed training sources"
  evidence_to_check:
    - "是否说明具体机器人、本体状态、动作空间和任务集合"
    - "官方 demo 是否对应论文实验，而不是单独展示"
    - "是否有公开 benchmark 或可复现实验脚本"
  resources:
    code: "https://github.com/Physical-Intelligence/openpi"
    blog: "https://www.pi.website/blog"
    checkpoint_and_data: "check openpi / model card / dataset card before planning reproduction"
  decision:
    action: "deep-read + engineering reference; reproduce only after hardware/data/protocol gate passes"
    reason: "入口完整度高，但复现仍依赖机器人本体、数据格式、算力、权重和评测协议"
```

这个示例的关键不是评价 π0.5 好坏，而是练习一个读法：先把论文、官方博客和开源仓库串起来，再决定它在课程中属于“模型导读、工程框架参考、还是可复现实验”。

Sources:
- [arXiv Robotics recent papers](https://arxiv.org/list/cs.RO/recent)
- [OpenReview](https://openreview.net/)
- [RSS Proceedings](https://www.roboticsproceedings.org/)
- [PMLR](https://proceedings.mlr.press/)
- [CVF Open Access](https://openaccess.thecvf.com/)
- [DBLP](https://dblp.org/)
- [Semantic Scholar API](https://www.semanticscholar.org/product/api)
- [Embodied-AI-Guide Useful Info](https://github.com/TianxingChen/Embodied-AI-Guide)
- [π0.5 arXiv](https://arxiv.org/abs/2504.16054)
- [Physical Intelligence Blog](https://www.pi.website/blog)
- [Physical-Intelligence/openpi](https://github.com/Physical-Intelligence/openpi)

- 返回本章：[研究生态](README.md)
