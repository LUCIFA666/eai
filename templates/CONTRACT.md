# 模板 / 主题契约（接口）

`serve_docs.py` 把内容（`section/**/*.md`）渲染成**语义化 HTML**，再填进模板 `page.html`，最后由主题
`static/base.css` + `static/highlight.css` 上样式。三层只靠本契约对接：

> **只要新模板/新主题实现下面的占位符与 class，就能任意替换，且不需要改动任何 `.md`。**
> 反过来，新增或修改 `.md` 也不需要改模板与主题。

## 1. 模板占位符（`templates/page.html`）

渲染时按字符串替换填入，全部必须存在：

| 占位符 | 内容 |
|---|---|
| `{{title}}` | 当前页标题（已含派生序号），用于 `<title>` |
| `{{breadcrumb}}` | 当前页相对路径（面包屑） |
| `{{nav}}` | 侧边栏导航 HTML（见下面的 class） |
| `{{body}}` | 正文 HTML |
| `{{prevnext}}` | 服务器自动生成的「上一节/下一节/返回本章」块 |

模板需引入 `/static/base.css`、`/static/highlight.css`，并 `<script src="/static/reload.js">`（自动刷新，可选）。

## 2. 渲染器产出的语义 class（主题按这些选择器取样式）

**侧边栏导航**
- `.home-link` 顶部「课程首页 / 章节总览」链接
- `.chapter-group`（`<details>`）/ `.chapter-link`（章标题链接）
- `.lesson-list` 章内小节容器
- `.subchapter-group`（`<details>`）/ `.subchapter-parent`（二级标题链接）
- `.lesson-tree-group.level-N`（`<details>`，三级及更深）/ `.nested-lesson-list`
- `.lesson-link`、`.lesson-link.nested[.level-2|.level-3]`、`.lesson-link.tree-parent`
- `.lesson-link.active` 当前页高亮

**正文**
- 标题 `h1`–`h6`（`h1` 文本已被注入派生序号，如 `4.5 视觉基础模型`）
- 表格 `.table-wrap > table > thead/tbody`
- 代码块 `pre.code-block > code`，高亮 span：`.syntax-keyword/.syntax-builtin/.syntax-string/.syntax-number/.syntax-comment/.syntax-heading`
- 图片 `img.doc-img`（不再使用内联 style）
- 内嵌图示 `.doc-figure`、`.doc-figure-title`、`.doc-figure-subtitle`、`.figure-grid[.wide]`、`.figure-flow`、`.figure-pipeline`（横向流水线容器，也可与 `.doc-figure` 同挂在 `<figure>` 上）、`.figure-node`、`.figure-node.tone-green/blue/gold/rose`（节点配色）、`.figure-note`（图示底部注解）
- 自动小节目录 `.auto-toc`（`<!-- AUTO-TOC -->` 占位符展开）

**自动导航块**
- `.page-nav`，内含 `.nav-prev` / `.nav-next` / `.nav-up` 链接

## 3. 约定（内容侧）

- 文件名 `NN-` 前缀决定顺序；显示序号由文件系统位置自动派生，正文标题**不必**手写序号。
- 每页图片放在与该页同名目录下的 `assets/`，如 `01-camera-calibration/assets/foo.png`，引用写相对路径。
- 章 README 或 `section/README.md` 里写 `<!-- AUTO-TOC -->` 即可自动生成目录。
