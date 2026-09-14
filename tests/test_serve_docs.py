from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import serve_docs


class DocsServerTests(unittest.TestCase):
    # ----- URL resolution & security ------------------------------------- #

    def test_resolves_root_chapter_and_markdown_paths(self) -> None:
        self.assertEqual(serve_docs.resolve_doc_path("/", ROOT), ROOT / "README.md")
        self.assertEqual(
            serve_docs.resolve_doc_path("/section/01-introduction/", ROOT),
            ROOT / "section/01-introduction/README.md",
        )
        self.assertEqual(
            serve_docs.resolve_doc_path(
                "/section/01-introduction/01-embodied-ai-landscape.md", ROOT
            ),
            ROOT / "section/01-introduction/01-embodied-ai-landscape.md",
        )

    def test_rejects_path_traversal_and_non_markdown_pages(self) -> None:
        self.assertIsNone(serve_docs.resolve_doc_path("/../requirements.txt", ROOT))
        self.assertIsNone(serve_docs.resolve_doc_path("/requirements.txt", ROOT))

    # ----- markdown rendering (unchanged contract) ----------------------- #

    def test_markdown_tables_render_as_html_tables(self) -> None:
        html = serve_docs.render_markdown(
            "| 字段 | 说明 |\n|---|---|\n| `task_id` | 任务标识 |", ROOT / "README.md", ROOT
        )
        self.assertIn("<table>", html)
        self.assertIn("<th>字段</th>", html)
        self.assertIn("<td><code>task_id</code></td>", html)
        self.assertNotIn("<p>| 字段 | 说明 |</p>", html)

    def test_python_code_blocks_render_with_light_syntax_highlighting(self) -> None:
        html = serve_docs.render_markdown(
            '```python\nif value > 1:\n    print("ok")\n```\n', ROOT / "README.md", ROOT
        )
        self.assertIn('<pre class="code-block language-python">', html)
        self.assertIn('<span class="syntax-keyword">if</span>', html)
        self.assertIn('<span class="syntax-builtin">print</span>', html)
        self.assertIn('<span class="syntax-string">&quot;ok&quot;</span>', html)
        # syntax colours live in static/highlight.css, never inline in the markup
        self.assertNotIn("background:", html)

    def test_display_math_stays_in_one_dom_container_for_katex(self) -> None:
        html = serve_docs.render_markdown(
            "$$\n\\mathbf{x}=\\begin{bmatrix}p\\\\v\\end{bmatrix}\n$$\n",
            ROOT / "README.md",
            ROOT,
        )
        self.assertIn('<div class="math-block">$$\n', html)
        self.assertIn(r"\mathbf{x}=\begin{bmatrix}p\\v\end{bmatrix}", html)
        self.assertNotIn("<p>$$</p>", html)

    def test_markdown_images_render_with_doc_img_class(self) -> None:
        html = serve_docs.render_markdown(
            "![VLA 基础导图](section/07-vlm-vla-and-foundation-models/assets/vla-foundations-map.svg)",
            ROOT / "README.md",
            ROOT,
        )
        self.assertIn('<img class="doc-img"', html)
        self.assertIn(
             'src="/section/07-vlm-vla-and-foundation-models/assets/vla-foundations-map.svg"', html
        )
        self.assertNotIn("style=", html)

    def test_raw_html_diagrams_render_as_html(self) -> None:
        html = serve_docs.render_markdown(
            '<figure class="doc-figure figure-map"><p class="doc-figure-title">测试图</p></figure>',
            ROOT / "README.md",
            ROOT,
        )
        self.assertIn('class="doc-figure figure-map"', html)
        self.assertIn("测试图", html)

    # ----- external template / theme (modularity) ------------------------ #

    def test_page_uses_external_template_and_stylesheets(self) -> None:
        doc_path = ROOT / "section/01-introduction/01-embodied-ai-landscape.md"
        html = serve_docs.render_page(doc_path, ROOT)

        self.assertIn("动手学具身 AI", html)
        self.assertIn('<link rel="stylesheet" href="/static/base.css"', html)
        self.assertIn('<link rel="stylesheet" href="/static/highlight.css"', html)
        self.assertIn('src="/static/reload.js"', html)
        # CSS is no longer inlined in the page
        self.assertNotIn("<style>", html)
        # template slots are fully filled
        for slot in ("{{title}}", "{{nav}}", "{{body}}", "{{breadcrumb}}", "{{prevnext}}"):
            self.assertNotIn(slot, html)

    def test_static_stylesheets_and_script_are_servable(self) -> None:
        self.assertIn(".css", serve_docs.ALLOWED_STATIC_SUFFIXES)
        self.assertIn(".js", serve_docs.ALLOWED_STATIC_SUFFIXES)
        for rel in ("static/base.css", "static/highlight.css", "static/reload.js"):
            self.assertEqual(
                serve_docs.resolve_static_path("/" + rel, ROOT), ROOT / rel, rel
            )

    def test_webm_video_assets_are_servable(self) -> None:
        rel = (
            "section/04-planning-control-and-baselines/"
            "02-planning-tools-and-practice/02-curobo-practice/"
            "assets/get-started-motion-plan.webm"
        )
        self.assertIn(".webm", serve_docs.ALLOWED_STATIC_SUFFIXES)
        self.assertEqual(
            serve_docs.resolve_static_path("/" + rel, ROOT), ROOT / rel
        )
        self.assertEqual(serve_docs.mimetypes.guess_type(rel)[0], "video/webm")

    def test_webp_image_assets_are_servable(self) -> None:
        rel = (
            "section/04-planning-control-and-baselines/"
            "02-planning-tools-and-practice/03-rmpflow-practice/"
            "assets/rmpflow-tutorial-ui.webp"
        )
        self.assertIn(".webp", serve_docs.ALLOWED_STATIC_SUFFIXES)
        self.assertEqual(
            serve_docs.resolve_static_path("/" + rel, ROOT), ROOT / rel
        )
        self.assertEqual(serve_docs.mimetypes.guess_type(rel)[0], "image/webp")

    # ----- filesystem-derived numbering --------------------------------- #

    def test_number_derivation_matches_filesystem(self) -> None:
        cases = {
            "section/03-perception-and-3d-vision/01-geometric-perception-foundations/02-hand-eye-calibration.md": "3.1.2",
            # inserted/expanded perception nodes renumber automatically by position
            "section/03-perception-and-3d-vision/01-geometric-perception-foundations/05-3d-reconstruction.md": "3.1.5",
            "section/03-perception-and-3d-vision/03-vision-foundation-models.md": "3.3",
            "section/03-perception-and-3d-vision/04-interactive-perception/04-grasp-pose-generation.md": "3.4.4",
            "section/03-perception-and-3d-vision/05-spatial-localization-and-semantic-maps/01-spatial-localization-mapping.md": "3.5.1",
            "section/03-perception-and-3d-vision/06-perception-interface-and-closed-loop/01-perception-interface.md": "3.6.1",
            "section/07-vlm-vla-and-foundation-models/01-vla-foundations/01-before-vla-vision-action.md": "7.1.1",
            "section/09-reinforcement-learning-for-robotics/03-rlinf-vla-rl/README.md": "9.3.0",
            # orphan subdir page folds into the parent's numbering
            "section/09-reinforcement-learning-for-robotics/04-simplevla-rl/hands-on/01-simplevla-rl.md": "9.4.12",
        }
        for rel, expected in cases.items():
            self.assertEqual(serve_docs.number_for_doc(ROOT / rel), expected, rel)
        # chapter README keeps the two-digit chapter number
        self.assertEqual(
            serve_docs.number_for_doc(ROOT / "section/03-perception-and-3d-vision/README.md"),
            "03",
        )

    def test_h1_number_is_injected_from_filesystem(self) -> None:
        doc_path = ROOT / "section/03-perception-and-3d-vision/03-vision-foundation-models.md"
        html = serve_docs.render_page(doc_path, ROOT)
        title = serve_docs.clean_title(doc_path)
        self.assertIn(f">3.3 {title}</h1>", html)
        # the number must not be duplicated even though the source heading carries one
        self.assertNotIn("3.3 3.3", html)

    def test_auxiliary_notes_are_not_surfaced(self) -> None:
        nav = serve_docs.build_navigation(ROOT, ROOT / "README.md")
        self.assertNotIn("/section/03-perception-and-3d-vision/improve.md", nav)
        self.assertNotIn("/section/03-perception-and-3d-vision/summary.md", nav)
        self.assertIsNone(
            serve_docs.number_for_doc(ROOT / "section/03-perception-and-3d-vision/improve.md")
        )

    # ----- navigation tree ---------------------------------------------- #

    def test_navigation_lists_every_chapter_with_derived_label(self) -> None:
        nav = serve_docs.build_navigation(ROOT, ROOT / "README.md")
        self.assertIn("章节总览", nav)
        chapters = list(serve_docs.chapter_dirs(ROOT))
        self.assertEqual(nav.count("chapter-link"), len(chapters))
        for chapter in chapters:
            label = f"{serve_docs.chapter_number(chapter)} {serve_docs.clean_title(chapter / 'README.md')}"
            self.assertIn(label, nav)

    def test_navigation_uses_derived_section_numbers(self) -> None:
        nav = serve_docs.build_navigation(ROOT, ROOT / "README.md")
        samples = {
            "section/03-perception-and-3d-vision/03-vision-foundation-models.md": "3.3",
            "section/05-simulation-and-task-modeling/02-mujoco.md": "5.2",
            "section/07-vlm-vla-and-foundation-models/01-vla-foundations.md": "7.1",
            "section/09-reinforcement-learning-for-robotics/01-foundations.md": "9.1",
        }
        for rel, number in samples.items():
            label = f"{number} {serve_docs.clean_title(ROOT / rel)}"
            self.assertIn(label, nav)
            self.assertIn(f'href="/{rel}"', nav)

    def test_leaf_second_level_lessons_render_as_collapsible_groups(self) -> None:
        nav = serve_docs.build_navigation(ROOT, ROOT / "README.md")
        self.assertRegex(
            nav,
            re.compile(
                r'<details class="subchapter-group"[^>]*>\n'
                r'<summary><a class="lesson-link subchapter-parent[^"]*" '
                r'href="/section/01-introduction/01-embodied-ai-landscape\.md">'
            ),
        )

    def test_leaf_third_level_lessons_render_as_collapsible_groups(self) -> None:
        nav = serve_docs.build_navigation(ROOT, ROOT / "README.md")
        self.assertRegex(
            nav,
            re.compile(
                r'<details class="lesson-tree-group level-1"[^>]*>\n'
                r'<summary><a class="lesson-link nested tree-parent level-1[^"]*" '
                r'href="/section/02-robotics-foundations/02-model-assets-and-body-description/01-urdf-mjcf-usd\.md">'
            ),
        )

    def test_orphan_fourth_level_page_folds_under_third_level_parent(self) -> None:
        nav = serve_docs.build_navigation(ROOT, ROOT / "README.md")
        target = (
            "/section/09-reinforcement-learning-for-robotics/04-simplevla-rl/"
            "hands-on/01-simplevla-rl.md"
        )
        target_pos = nav.index(target)
        tree_start = nav.rfind(
            '<details class="lesson-tree-group level-1"', 0, target_pos
        )
        group = nav[tree_start : nav.index("</details>", target_pos)]
        self.assertIn('class="lesson-tree-group level-1"', group)
        self.assertIn("9.4.12", group)
        self.assertIn(target, group)

    def test_active_fourth_level_page_opens_recursive_parents(self) -> None:
        active = ROOT / (
            "section/09-reinforcement-learning-for-robotics/04-simplevla-rl/"
            "hands-on/01-simplevla-rl.md"
        )
        nav = serve_docs.build_navigation(ROOT, active)
        self.assertIn('class="lesson-tree-group level-1" open', nav)
        self.assertIn(
            'class="lesson-link nested tree-parent level-1 active" '
            'href="/section/09-reinforcement-learning-for-robotics/'
            '04-simplevla-rl/hands-on/01-simplevla-rl.md"',
            nav,
        )

    def test_navigation_keeps_all_lesson_pages_reachable(self) -> None:
        nav = serve_docs.build_navigation(ROOT, ROOT / "README.md")
        hrefs = set(re.findall(r'href="([^"]+)"', nav))
        missing = []
        for page in sorted((ROOT / "section").rglob("*.md")):
            relative = page.relative_to(ROOT).as_posix()
            if "/inventory/" in f"/{relative}":
                continue
            # auxiliary notes without an NN- prefix are intentionally not lessons
            if page.name != "README.md" and not re.match(r"^\d+-", page.name):
                continue
            # the chapter-overview README is reached via the chapter link / home links
            if page.parent.parent == ROOT / "section" and page.name == "README.md":
                continue
            if page.parent == ROOT / "section":  # section/README.md (home link)
                continue
            if f"/{relative}" not in hrefs:
                missing.append(relative)
        self.assertEqual(missing, [])

    # ----- auto table of contents & prev/next --------------------------- #

    def test_auto_toc_placeholder_expands_in_chapter_readme(self) -> None:
        doc = ROOT / "section/03-perception-and-3d-vision/README.md"
        html = serve_docs.render_markdown("<!-- AUTO-TOC -->", doc, ROOT)
        self.assertIn('class="auto-toc"', html)
        self.assertIn("3.3", html)
        self.assertIn("/section/03-perception-and-3d-vision/03-vision-foundation-models.md", html)
        self.assertIn("3.6", html)

    def test_auto_toc_lists_chapters_on_section_readme(self) -> None:
        toc = serve_docs.render_auto_toc(ROOT / "section/README.md", ROOT)
        self.assertIn('class="auto-toc"', toc)
        self.assertIn("/section/03-perception-and-3d-vision/README.md", toc)

    def test_prevnext_follows_reading_order(self) -> None:
        doc = ROOT / "section/03-perception-and-3d-vision/03-vision-foundation-models.md"
        pn = serve_docs.render_prevnext(doc, ROOT)
        self.assertIn('class="page-nav"', pn)
        self.assertIn("上一节", pn)
        self.assertIn("章节首页", pn)
        self.assertIn("下一节", pn)
        # depth-first order: 3.2.7 (foundationpose) -> 3.3 (vfm) -> 3.3.1 (clip)
        self.assertIn(
            "/section/03-perception-and-3d-vision/02-object-perception/07-foundationpose.md", pn
        )
        self.assertIn(
            "/section/03-perception-and-3d-vision/03-vision-foundation-models/01-clip-and-siglip.md",
            pn,
        )

    # ----- auto-reload endpoint ----------------------------------------- #

    def test_mtime_endpoint_reports_chapter_freshness(self) -> None:
        mtime = serve_docs.compute_mtime(
            "/section/03-perception-and-3d-vision/03-vision-foundation-models.md", ROOT
        )
        self.assertGreater(mtime, 0)


if __name__ == "__main__":
    unittest.main()
