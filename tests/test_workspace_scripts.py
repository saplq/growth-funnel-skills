from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "designing-growth-funnels"
SCRIPTS = SKILL / "scripts"


def run_script(name: str, *args: str, input_text: str | None = None) -> dict:
    command = [sys.executable, str(SCRIPTS / name), *args]
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"{name} failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return json.loads(result.stdout)


def assert_final_pack(workspace: Path) -> None:
    final_dir = workspace / "final"
    expected = [
        "00_index.md",
        "00_index.html",
        "01_status_next_steps.md",
        "01_status_next_steps.html",
        "02_funnel_blueprint.md",
        "02_funnel_blueprint.html",
        "03_screen_specs.md",
        "03_screen_specs.html",
        "04_tracking_plan.md",
        "04_tracking_plan.html",
        "05_experiment_card.md",
        "05_experiment_card.html",
        "06_postmortem_template.md",
        "06_postmortem_template.html",
        "index.html",
    ]
    for filename in expected:
        path = final_dir / filename
        if not path.exists():
            raise AssertionError(f"missing final file: {path}")
        if path.stat().st_size == 0:
            raise AssertionError(f"empty final file: {path}")
    forbidden = {".yaml", ".yml", ".csv"}
    for path in final_dir.iterdir():
        if path.suffix in forbidden:
            raise AssertionError(f"raw file leaked into final pack: {path}")
    for md_path in final_dir.glob("*.md"):
        html_path = md_path.with_suffix(".html")
        if not html_path.exists():
            raise AssertionError(f"missing html pair for {md_path}")
        if md_path.read_text(encoding="utf-8").startswith("---"):
            raise AssertionError(f"frontmatter leaked into final markdown: {md_path}")
    for html_path in final_dir.glob("*.html"):
        html = html_path.read_text(encoding="utf-8").lower()
        if "<style" in html or "stylesheet" in html:
            raise AssertionError(f"css leaked into final html: {html_path}")


class WorkspaceScriptsTest(unittest.TestCase):
    def test_empty_workspace_has_low_score_and_all_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "empty"
            summary = run_script(
                "create_workspace.py",
                "--name",
                "Empty test",
                "--out",
                str(workspace),
            )

            self.assertLess(summary["completeness_score"], 20)
            self.assertIn("offer", summary["critical_missing_fields"])
            self.assertLessEqual(len(summary["next_best_input"]), 3)
            for filename in [
                "00_status.md",
                "01_intake_brief.yaml",
                "02_proof_library.csv",
                "03_current_metrics.csv",
                "04_channel_context.yaml",
                "05_segment_profile.yaml",
                "06_funnel_blueprint.md",
                "07_screen_specs.md",
                "08_tracking_plan.csv",
                "09_experiment_card.md",
                "10_postmortem_record.md",
                "11_presentation.html",
            ]:
                self.assertTrue((workspace / filename).exists(), filename)

    def test_partial_notes_update_structured_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "partial"
            run_script("create_workspace.py", "--name", "Partial", "--out", str(workspace))
            result = run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                input_text=(
                    "Offer: AI CRM cleanup for agencies\n"
                    "ICP: agency owners\n"
                    "Channel: cold outbound\n"
                ),
            )

            self.assertIn("offer", result["changed"]["intake"])
            self.assertIn("icp", result["changed"]["intake"])
            self.assertIn("primary_channel", result["changed"]["channel"])
            self.assertIn("target KPI", result["summary"]["critical_missing_fields"])

    def test_missing_target_kpi_blocks_experiment_card(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "blocked"
            run_script("create_workspace.py", "--name", "Blocked", "--out", str(workspace))
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                input_text=(
                    "Offer: onboarding audit\n"
                    "ICP: SaaS founders\n"
                    "Channel: LinkedIn\n"
                    "No proof yet\n"
                ),
            )
            result = run_script("render_outputs.py", str(workspace))

            self.assertFalse(result["rendered"])
            self.assertEqual(
                result["summary"]["artifact_status"]["09_experiment_card.md"],
                "blocked",
            )
            assert_final_pack(workspace)
            self.assertIn("final_index_path", result["summary"])

    def test_no_proof_flag_allows_render_but_lowers_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "no-proof"
            run_script("create_workspace.py", "--name", "No proof", "--out", str(workspace))
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                input_text=(
                    "Offer: weekly conversion audits\n"
                    "ICP: SaaS founders\n"
                    "Target KPI: trial activation\n"
                    "Channel: LinkedIn content\n"
                    "No proof yet\n"
                ),
            )
            result = run_script("render_outputs.py", str(workspace))

            self.assertTrue(result["rendered"])
            self.assertTrue(result["summary"]["minimum_gate_satisfied"])
            self.assertLess(result["summary"]["qualification_score"], 70)
            assert_final_pack(workspace)
            tracking = (workspace / "final" / "04_tracking_plan.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("First Value Reached", tracking)

    def test_conflicting_proof_state_appears_in_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "conflict"
            run_script("create_workspace.py", "--name", "Conflict", "--out", str(workspace))
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                input_text=(
                    "Offer: churn dashboard\n"
                    "ICP: SaaS operators\n"
                    "Target KPI: first value reached\n"
                    "Channel: search\n"
                    "No proof yet\n"
                    "Proof: customer demo showed 18% churn recovery\n"
                ),
            )
            summary = run_script("validate_workspace.py", str(workspace), "--json")

            self.assertTrue(summary["contradictions"])
            self.assertIn("explicit_no_proof_yet", summary["contradictions"][0])
            status = (workspace / "00_status.md").read_text(encoding="utf-8")
            self.assertIn("Proof rows exist", status)

    def test_russian_notes_set_language_and_render_presentation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "russian"
            created = run_script(
                "create_workspace.py",
                "--name",
                "Russian",
                "--out",
                str(workspace),
                "--language",
                "Russian",
            )
            self.assertEqual(created["output_language"], "Russian")
            initial_status = (workspace / "00_status.md").read_text(encoding="utf-8")
            initial_html = (workspace / "11_presentation.html").read_text(encoding="utf-8")
            self.assertIn("# Статус funnel workspace", initial_status)
            self.assertIn("оффер", initial_status)
            self.assertIn("Презентация growth funnel", initial_html)
            self.assertIn("Следующий ввод", initial_html)
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                input_text=(
                    "Оффер: аудит онбординга для SaaS\n"
                    "ICP: основатели SaaS\n"
                    "Целевой KPI: активация триала\n"
                    "Канал: LinkedIn content\n"
                    "Нет доказательств\n"
                ),
            )
            result = run_script("render_outputs.py", str(workspace))

            self.assertTrue(result["rendered"])
            self.assertEqual(result["summary"]["output_language"], "Russian")
            html = (workspace / "11_presentation.html").read_text(encoding="utf-8")
            self.assertIn("Презентация growth funnel", html)
            blueprint = (workspace / "06_funnel_blueprint.md").read_text(encoding="utf-8")
            self.assertIn("# Blueprint воронки", blueprint)
            assert_final_pack(workspace)
            final_index = (workspace / "final" / "00_index.md").read_text(encoding="utf-8")
            self.assertIn("Итоговый пакет", final_index)
            self.assertIn("Читать по порядку", final_index)
            self.assertIn("Blueprint воронки", final_index)
            final_status = (workspace / "final" / "01_status_next_steps.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Оценка полноты", final_status)
            self.assertIn("Минимальный набор вводных", final_status)
            final_tracking = (workspace / "final" / "04_tracking_plan.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("| Событие | Этап | Назначение |", final_tracking)
            final_html = (workspace / "final" / "index.html").read_text(encoding="utf-8")
            self.assertIn("<title>Оглавление</title>", final_html)


if __name__ == "__main__":
    unittest.main()
