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
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{name} did not return JSON:\n{result.stdout}") from exc


def assert_runtime_contract(workspace: Path) -> None:
    runtime = workspace / "runtime"
    expected = [
        "run_state.json",
        "intake.json",
        "topics.json",
        "agent_tasks.json",
        "agent_results.jsonl",
        "sources.jsonl",
        "competitors.csv",
        "gaps.json",
    ]
    for filename in expected:
        path = runtime / filename
        if not path.exists():
            raise AssertionError(f"missing runtime file: {path}")


def assert_final_pack(workspace: Path) -> None:
    final_dir = workspace / "final"
    expected = [
        "index.html",
        "00_index.md",
        "00_index.html",
        "01_status_next_steps.md",
        "01_status_next_steps.html",
        "02_intake_brief.md",
        "02_intake_brief.html",
        "03_research_evidence.md",
        "03_research_evidence.html",
        "04_competitor_map.md",
        "04_competitor_map.html",
        "05_funnel_blueprint.md",
        "05_funnel_blueprint.html",
        "06_screen_specs.md",
        "06_screen_specs.html",
        "07_tracking_plan.md",
        "07_tracking_plan.html",
        "08_experiment_card.md",
        "08_experiment_card.html",
        "09_risks_and_gaps.md",
        "09_risks_and_gaps.html",
        "10_execution_plan.md",
        "10_execution_plan.html",
    ]
    for filename in expected:
        path = final_dir / filename
        if not path.exists():
            raise AssertionError(f"missing final file: {path}")
        if path.stat().st_size == 0:
            raise AssertionError(f"empty final file: {path}")
    forbidden = {".json", ".jsonl", ".csv", ".yaml", ".yml", ".css"}
    for path in final_dir.iterdir():
        if path.suffix in forbidden:
            raise AssertionError(f"raw runtime file leaked into final: {path}")
    for md_path in final_dir.glob("*.md"):
        if md_path.read_text(encoding="utf-8").startswith("---"):
            raise AssertionError(f"frontmatter leaked into final markdown: {md_path}")
        html_path = md_path.with_suffix(".html")
        if not html_path.exists():
            raise AssertionError(f"missing HTML pair for {md_path}")
    for html_path in final_dir.glob("*.html"):
        html = html_path.read_text(encoding="utf-8")
        if "<style>" not in html:
            raise AssertionError(f"missing inline style: {html_path}")
        if "stylesheet" in html.lower():
            raise AssertionError(f"external stylesheet reference leaked: {html_path}")


class WorkspaceScriptsTest(unittest.TestCase):
    def test_empty_workspace_creates_runtime_and_low_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "empty"
            summary = run_script(
                "create_workspace.py",
                "--name",
                "Empty test",
                "--out",
                str(workspace),
                "--json",
            )

            assert_runtime_contract(workspace)
            self.assertLess(summary["completeness_score"], 20)
            self.assertIn("offer", summary["critical_missing_fields"])
            self.assertLessEqual(len(summary["next_best_input"]), 3)
            self.assertEqual(summary["source_count"], 0)
            self.assertEqual(summary["competitor_count"], 0)
            self.assertIn("source registry has no current sources", summary["evidence_gaps"])

    def test_partial_notes_update_intake_and_keep_gate_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "partial"
            run_script("create_workspace.py", "--name", "Partial", "--out", str(workspace), "--json")
            result = run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--kind",
                "notes",
                "--json",
                input_text=(
                    "Offer: AI CRM cleanup for agencies\n"
                    "ICP: agency owners\n"
                    "Channel: cold outbound\n"
                ),
            )

            self.assertIn("offer", result["changed"]["intake"])
            self.assertIn("icp", result["changed"]["intake"])
            self.assertIn("primary_channel", result["changed"]["intake"])
            self.assertIn("target_kpi", result["summary"]["critical_missing_fields"])
            self.assertFalse(result["summary"]["minimum_gate_satisfied"])

    def test_rich_notes_render_ready_final_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "rich"
            run_script("create_workspace.py", "--name", "Rich", "--out", str(workspace), "--json")
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=(
                    "Offer: connect Stripe and see churn risks in 3 minutes\n"
                    "ICP: SaaS operators\n"
                    "Target KPI: First Value Reached / Trial Started\n"
                    "Channel: search\n"
                    "TTFV: 3\n"
                    "Proof: customer case showed 18% churn recovery\n"
                    "Metric: trial activation 22% last month\n"
                ),
            )
            result = run_script("render_final.py", str(workspace), "--json")

            self.assertTrue(result["minimum_gate_satisfied"])
            self.assertTrue(result["rendered"])
            assert_final_pack(workspace)
            tracking = (workspace / "final" / "07_tracking_plan.md").read_text(encoding="utf-8")
            self.assertIn("First Value Reached", tracking)
            blueprint = (workspace / "final" / "05_funnel_blueprint.md").read_text(encoding="utf-8")
            self.assertIn("trial_to_value", blueprint)

    def test_no_proof_flag_allows_gate_but_lowers_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "no-proof"
            run_script("create_workspace.py", "--name", "No proof", "--out", str(workspace), "--json")
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=(
                    "Offer: weekly conversion audits\n"
                    "ICP: SaaS founders\n"
                    "Target KPI: trial activation\n"
                    "Channel: LinkedIn content\n"
                    "No proof yet\n"
                ),
            )
            result = run_script("render_final.py", str(workspace), "--json")

            self.assertTrue(result["minimum_gate_satisfied"])
            self.assertLess(result["qualification_score"], 70)
            assert_final_pack(workspace)
            experiment = (workspace / "final" / "08_experiment_card.md").read_text(encoding="utf-8")
            self.assertIn("trial activation", experiment)

    def test_conflicting_proof_state_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "conflict"
            run_script("create_workspace.py", "--name", "Conflict", "--out", str(workspace), "--json")
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
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

    def test_source_and_competitor_ingestion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "research"
            run_script("create_workspace.py", "--name", "Research", "--out", str(workspace), "--json")
            result = run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--kind",
                "competitor",
                "--json",
                input_text=(
                    "Source: Pricing page https://example.com/pricing retrieved 2026-05-15\n"
                    "Competitor: RivalOne | domain: rivalone.com | pricing: $29/mo | "
                    "positioning: analytics for SaaS teams | CTA: Start free | "
                    "onboarding: connect Stripe | source: https://rivalone.com/pricing | "
                    "retrieved: 2026-05-15\n"
                ),
            )

            self.assertEqual(result["changed"]["source_rows_added"], 2)
            self.assertEqual(result["changed"]["competitor_rows_added"], 1)
            self.assertEqual(result["summary"]["source_count"], 2)
            self.assertEqual(result["summary"]["competitor_count"], 1)
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(source_rows[0]["publisher"], "example.com")
            competitor_csv = (workspace / "runtime" / "competitors.csv").read_text(encoding="utf-8")
            self.assertIn("RivalOne", competitor_csv)
            self.assertIn("Start free", competitor_csv)

    def test_duplicate_notes_report_only_actual_new_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "duplicates"
            run_script("create_workspace.py", "--name", "Duplicates", "--out", str(workspace), "--json")
            notes = (
                "Offer: conversion audit\n"
                "ICP: SaaS founders\n"
                "Target KPI: trial activation\n"
                "Channel: LinkedIn\n"
                "Proof: demo cohort improved activation by 12%\n"
                "Metric: activation 24%\n"
            )
            first = run_script("ingest_notes.py", str(workspace), "--input", "-", "--json", input_text=notes)
            second = run_script("ingest_notes.py", str(workspace), "--input", "-", "--json", input_text=notes)

            self.assertEqual(first["changed"]["proof_assets_added"], 1)
            self.assertEqual(first["changed"]["metrics_added"], 2)
            self.assertEqual(second["changed"]["proof_assets_added"], 0)
            self.assertEqual(second["changed"]["metrics_added"], 0)

    def test_record_agent_result_adds_result_and_citation_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "agent"
            run_script("create_workspace.py", "--name", "Agent", "--out", str(workspace), "--json")
            payload = {
                "role": "research",
                "topic_id": "research_evidence",
                "task_id": "research-1",
                "summary": "Pricing pages emphasize fast setup.",
                "key_findings": ["Fast setup is a repeated promise."],
                "citations": [{"url": "https://example.com/research", "title": "Research"}],
                "freshness_date": "2026-05-15",
                "confidence": "medium",
                "open_questions": [],
                "next_action": "Collect competitors",
            }
            result = run_script(
                "record_agent_result.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=json.dumps(payload),
            )

            self.assertEqual(result["changed"]["agent_results_added"], 1)
            self.assertEqual(result["changed"]["source_rows_added"], 1)
            self.assertEqual(result["summary"]["source_count"], 1)

    def test_record_agent_result_updates_existing_source_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "agent-provenance"
            run_script("create_workspace.py", "--name", "Agent provenance", "--out", str(workspace), "--json")
            base_payload = {
                "role": "research",
                "topic_id": "research_evidence",
                "task_id": "research-1",
                "summary": "Pricing pages emphasize fast setup.",
                "citations": [{"url": "https://example.com/research", "title": "Research"}],
                "confidence": "unknown",
            }
            dated_payload = dict(base_payload)
            dated_payload["task_id"] = "research-2"
            dated_payload["freshness_date"] = "2026-05-15"
            dated_payload["confidence"] = "medium"

            first = run_script(
                "record_agent_result.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=json.dumps(base_payload),
            )
            second = run_script(
                "record_agent_result.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=json.dumps(dated_payload),
            )
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertIn("current_practice source missing retrieved_at", " ".join(first["summary"]["evidence_gaps"]))
            self.assertEqual(second["changed"]["source_rows_added"], 0)
            self.assertEqual(len(source_rows), 1)
            self.assertEqual(source_rows[0]["retrieved_at"], "2026-05-15")
            self.assertEqual(source_rows[0]["freshness"], "current")
            self.assertEqual(source_rows[0]["confidence"], "medium")

    def test_russian_language_renders_russian_final(self) -> None:
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
                "--json",
            )
            self.assertEqual(created["output_language"], "Russian")
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=(
                    "Оффер: аудит онбординга для SaaS\n"
                    "ICP: основатели SaaS\n"
                    "Целевой KPI: активация триала\n"
                    "Канал: LinkedIn content\n"
                    "Нет доказательств\n"
                ),
            )
            result = run_script("render_final.py", str(workspace), "--json")

            self.assertEqual(result["output_language"], "Russian")
            assert_final_pack(workspace)
            final_index = (workspace / "final" / "00_index.md").read_text(encoding="utf-8")
            self.assertIn("Итоговый пакет", final_index)
            status = (workspace / "final" / "01_status_next_steps.md").read_text(encoding="utf-8")
            self.assertIn("Оценка полноты", status)
            html = (workspace / "final" / "index.html").read_text(encoding="utf-8")
            self.assertIn("<title>Оглавление</title>", html)
            self.assertIn('<html lang="ru">', html)
            self.assertIn("index-grid", html)
            self.assertIn("Начать", html)
            page_html = (workspace / "final" / "00_index.html").read_text(encoding="utf-8")
            self.assertIn('<html lang="ru">', page_html)

    def test_create_is_idempotent_and_does_not_overwrite_intake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "idempotent"
            run_script("create_workspace.py", "--name", "First", "--out", str(workspace), "--json")
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text="Offer: durable funnel workspace\n",
            )
            run_script("create_workspace.py", "--name", "Second", "--out", str(workspace), "--json")
            intake = json.loads((workspace / "runtime" / "intake.json").read_text(encoding="utf-8"))

            self.assertEqual(intake["offer"], "durable funnel workspace")
            self.assertEqual(intake["project_name"], "First")

    def test_final_cleanup_removes_raw_leaks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "leaks"
            run_script("create_workspace.py", "--name", "Leaks", "--out", str(workspace), "--json")
            final = workspace / "final"
            (final / "bad.json").write_text("{}", encoding="utf-8")
            (final / "style.css").write_text("body{}", encoding="utf-8")
            result = run_script("render_final.py", str(workspace), "--json")

            self.assertEqual(result["final_leakage"], [])
            assert_final_pack(workspace)

    def test_blocked_final_pack_is_rendered_but_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "blocked"
            run_script("create_workspace.py", "--name", "Blocked", "--out", str(workspace), "--json")
            result = run_script("render_final.py", str(workspace), "--json")
            screen_specs = (workspace / "final" / "06_screen_specs.md").read_text(encoding="utf-8")
            tracking = (workspace / "final" / "07_tracking_plan.md").read_text(encoding="utf-8")

            self.assertTrue(result["rendered"])
            self.assertFalse(result["recommendations_ready"])
            self.assertFalse(result["minimum_gate_satisfied"])
            self.assertIn("Status: blocked", screen_specs)
            self.assertIn("Status: blocked", tracking)
            assert_final_pack(workspace)

    def test_render_does_not_write_through_final_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "symlink-final"
            outside = Path(tmp) / "outside.md"
            outside.write_text("keep", encoding="utf-8")
            run_script("create_workspace.py", "--name", "Symlink final", "--out", str(workspace), "--json")
            link = workspace / "final" / "00_index.md"
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlink unavailable: {exc}")

            run_script("render_final.py", str(workspace), "--json")

            self.assertEqual(outside.read_text(encoding="utf-8"), "keep")
            self.assertFalse(link.is_symlink())
            self.assertTrue(link.exists())

    def test_runtime_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "symlink-runtime"
            outside = Path(tmp) / "outside.json"
            outside.write_text('{"project_name":"outside"}\n', encoding="utf-8")
            run_script("create_workspace.py", "--name", "Symlink runtime", "--out", str(workspace), "--json")
            target = workspace / "runtime" / "intake.json"
            target.unlink()
            try:
                target.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlink unavailable: {exc}")

            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_workspace.py"), str(workspace), "--json"],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to read or write symlinked workspace path", result.stderr)
            self.assertEqual(outside.read_text(encoding="utf-8"), '{"project_name":"outside"}\n')


if __name__ == "__main__":
    unittest.main()
