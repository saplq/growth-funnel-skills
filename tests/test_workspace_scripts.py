from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "designing-growth-funnels"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))

from workspace_lib import semantic_evidence_quality, validate_insights_contract, validate_orchestration_contract  # noqa: E402


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
        "orchestration_contract.json",
        "sources.jsonl",
        "competitors.csv",
        "gaps.json",
        "insights.json",
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


def assert_launch_exports(workspace: Path) -> None:
    exports = workspace / "exports"
    expected = [
        "action_plan",
        "event_schema",
        "content_brief",
        "crm_handoff",
        "funnel_diff",
        "variant_bundles",
        "reviewer_approval",
        "orchestration_contract",
        "experiment_card",
    ]
    for stem in expected:
        for suffix in [".json", ".csv"]:
            path = exports / f"{stem}{suffix}"
            if not path.exists():
                raise AssertionError(f"missing launch export: {path}")
            if path.stat().st_size == 0:
                raise AssertionError(f"empty launch export: {path}")
    manifest = exports / "manifest.json"
    if not manifest.exists():
        raise AssertionError(f"missing launch export manifest: {manifest}")
    final = workspace / "final"
    if final.exists():
        for path in final.iterdir():
            if path.suffix in {".json", ".jsonl", ".csv", ".yaml", ".yml"}:
                raise AssertionError(f"machine-readable export leaked into final: {path}")


def assert_markdown_row_columns(text: str, needle: str, expected_columns: int) -> None:
    matches = [line for line in text.splitlines() if needle in line and line.strip().startswith("|")]
    if not matches:
        raise AssertionError(f"missing markdown table row containing {needle!r}")
    for line in matches:
        cells = line.strip().strip("|").split("|")
        if len(cells) != expected_columns:
            raise AssertionError(f"markdown table row has {len(cells)} columns, expected {expected_columns}: {line}")


def write_sources(workspace: Path, rows: list[dict]) -> None:
    path = workspace / "runtime" / "sources.jsonl"
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def read_source_rows(workspace: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evidence_source(
    index: int,
    domain: str,
    *,
    weight: str = "medium",
    confidence: str = "medium",
    freshness: str = "current",
    retrieved_at: str = "2026-05-15",
    source_type: str = "pricing",
) -> dict:
    return {
        "source_id": f"source-{index}",
        "url": f"https://{domain}/pricing",
        "title": f"{domain} pricing",
        "publisher": domain,
        "retrieved_at": retrieved_at,
        "source_type": source_type,
        "freshness": freshness,
        "confidence": confidence,
        "evidence_weight": weight,
        "publisher_type": "primary_or_official" if weight == "high" else "publisher",
        "used_in": ["research_evidence", "screen_playbook"],
    }


def seed_ready_intake_and_competitors(workspace: Path) -> None:
    run_script("create_workspace.py", "--name", "Evidence scoring", "--out", str(workspace), "--json")
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
            "Competitor: RivalOne | domain: rivalone.com | pricing: $29/mo | "
            "positioning: churn analytics | CTA: Start free | onboarding: connect Stripe | "
            "source: https://rivalone.com/pricing | retrieved: 2026-05-15\n"
            "Competitor: RivalTwo | domain: rivaltwo.com | pricing: $49/mo | "
            "positioning: revenue recovery | CTA: Book demo | onboarding: import billing data | "
            "source: https://rivaltwo.com/pricing | retrieved: 2026-05-15\n"
            "Competitor: RivalThree | domain: rivalthree.com | pricing: custom | "
            "positioning: retention workflows | CTA: View demo | onboarding: sample workspace | "
            "source: https://rivalthree.com/pricing | retrieved: 2026-05-15\n"
        ),
    )


def seed_rich_competitor_patterns(workspace: Path) -> None:
    run_script("create_workspace.py", "--name", "Competitor synthesis", "--out", str(workspace), "--json")
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
            "Competitor: RivalOne | domain: rivalone.com | positioning: churn analytics | pricing: $29/mo | "
            "CTA: Start free | onboarding: connect Stripe | proof: customer stories | "
            "first value: churn risk dashboard | weakness: slow setup | "
            "source: https://rivalone.com/pricing | retrieved: 2026-05-15\n"
            "Competitor: RivalTwo | domain: rivaltwo.com | positioning: revenue recovery | pricing: $49/mo | "
            "CTA: Book demo | onboarding: import billing data | proof: testimonial wall | "
            "first value: recovery forecast | weakness: demo gate | "
            "source: https://rivaltwo.com/pricing | retrieved: 2026-05-15\n"
            "Competitor: RivalThree | domain: rivalthree.com | positioning: retention workflows | pricing: custom | "
            "CTA: View demo | onboarding: sample workspace | proof: trust badges | "
            "first value: retention workflow preview | weakness: custom pricing opacity | "
            "source: https://rivalthree.com/pricing | retrieved: 2026-05-15\n"
        ),
    )


def seed_channel_workspace(workspace: Path, channel: str, *, language: str = "English") -> None:
    run_script("create_workspace.py", "--name", "Channel synthesis", "--out", str(workspace), "--language", language, "--json")
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
            f"Channel: {channel}\n"
            "TTFV: 3\n"
            "Proof: customer case showed 18% churn recovery\n"
            "Competitor: RivalOne | domain: rivalone.com | positioning: churn analytics | pricing: $29/mo | "
            "CTA: Start free | onboarding: connect Stripe | proof: customer stories | "
            "first value: churn risk dashboard | weakness: slow setup | "
            "source: https://rivalone.com/pricing | retrieved: 2026-05-15\n"
            "Competitor: RivalTwo | domain: rivaltwo.com | positioning: revenue recovery | pricing: $49/mo | "
            "CTA: Book demo | onboarding: import billing data | proof: testimonial wall | "
            "first value: recovery forecast | weakness: demo gate | "
            "source: https://rivaltwo.com/pricing | retrieved: 2026-05-15\n"
            "Competitor: RivalThree | domain: rivalthree.com | positioning: retention workflows | pricing: custom | "
            "CTA: View demo | onboarding: sample workspace | proof: trust badges | "
            "first value: retention workflow preview | weakness: custom pricing opacity | "
            "source: https://rivalthree.com/pricing | retrieved: 2026-05-15\n"
        ),
    )


def seed_promise_workspace(workspace: Path, *, offer: str, proof_line: str, channel: str = "search") -> None:
    run_script("create_workspace.py", "--name", "Promise proof", "--out", str(workspace), "--json")
    run_script(
        "ingest_notes.py",
        str(workspace),
        "--input",
        "-",
        "--json",
        input_text=(
            f"Offer: {offer}\n"
            "ICP: SaaS operators\n"
            "Target KPI: First Value Reached / Trial Started\n"
            f"Channel: {channel}\n"
            "TTFV: 3\n"
            f"{proof_line}\n"
            "Competitor: RivalOne | domain: rivalone.com | positioning: churn analytics | pricing: $29/mo | "
            "CTA: Start free | onboarding: connect Stripe | proof: customer stories | "
            "first value: churn risk dashboard | weakness: slow setup | "
            "source: https://rivalone.com/pricing | retrieved: 2026-05-15\n"
            "Competitor: RivalTwo | domain: rivaltwo.com | positioning: revenue recovery | pricing: $49/mo | "
            "CTA: Book demo | onboarding: import billing data | proof: testimonial wall | "
            "first value: recovery forecast | weakness: demo gate | "
            "source: https://rivaltwo.com/pricing | retrieved: 2026-05-15\n"
            "Competitor: RivalThree | domain: rivalthree.com | positioning: retention workflows | pricing: custom | "
            "CTA: View demo | onboarding: sample workspace | proof: trust badges | "
            "first value: retention workflow preview | weakness: custom pricing opacity | "
            "source: https://rivalthree.com/pricing | retrieved: 2026-05-15\n"
        ),
    )


class WorkspaceScriptsTest(unittest.TestCase):
    def test_install_skill_zip_contract_matches_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "install_skill.py"),
                    "zip",
                    "--out",
                    str(out_dir),
                    "--force",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            archive = out_dir / "designing-growth-funnels.zip"
            self.assertTrue(archive.exists())
            self.assertIn(str(archive), result.stdout)
            with zipfile.ZipFile(archive) as handle:
                names = set(handle.namelist())
            self.assertIn("designing-growth-funnels/SKILL.md", names)
            self.assertIn("designing-growth-funnels/scripts/render_final.py", names)
            self.assertFalse(any("__pycache__" in name or name.endswith(".pyc") for name in names))

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
                    "Competitor: RivalOne | domain: rivalone.com | pricing: $29/mo | "
                    "positioning: churn analytics | CTA: Start free | onboarding: connect Stripe | "
                    "source: https://rivalone.com/pricing | retrieved: 2026-05-15\n"
                    "Competitor: RivalTwo | domain: rivaltwo.com | pricing: $49/mo | "
                    "positioning: revenue recovery | CTA: Book demo | onboarding: import billing data | "
                    "source: https://rivaltwo.com/pricing | retrieved: 2026-05-15\n"
                    "Competitor: RivalThree | domain: rivalthree.com | pricing: custom | "
                    "positioning: retention workflows | CTA: View demo | onboarding: sample workspace | "
                    "source: https://rivalthree.com/pricing | retrieved: 2026-05-15\n"
                ),
            )
            result = run_script("render_final.py", str(workspace), "--json")

            self.assertTrue(result["minimum_gate_satisfied"])
            self.assertEqual(result["phase"], "ready")
            self.assertTrue(result["recommendations_ready"])
            self.assertTrue(result["rendered"])
            final_index_path = workspace.resolve() / "final" / "index.html"
            self.assertEqual(result["final_index_path"], str(final_index_path))
            self.assertEqual(result["final_index_chat_link"], f"[Open final HTML]({final_index_path})")
            assert_final_pack(workspace)
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            self.assertIn("decision_summary", insights)
            self.assertGreaterEqual(len(insights["screens"]), 3)
            for screen in insights["screens"]:
                self.assertTrue(screen.get("support"))
            tracking = (workspace / "final" / "07_tracking_plan.md").read_text(encoding="utf-8")
            self.assertIn("First Value Reached", tracking)
            blueprint = (workspace / "final" / "05_funnel_blueprint.md").read_text(encoding="utf-8")
            self.assertIn("trial_to_value", blueprint)

    def test_compiled_rich_insights_include_structured_contract_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "rich-contract"
            run_script("create_workspace.py", "--name", "Rich contract", "--out", str(workspace), "--json")
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
                    "Competitor: RivalOne | domain: rivalone.com | pricing: $29/mo | "
                    "positioning: churn analytics | CTA: Start free | onboarding: connect Stripe | "
                    "source: https://rivalone.com/pricing | retrieved: 2026-05-15\n"
                    "Competitor: RivalTwo | domain: rivaltwo.com | pricing: $49/mo | "
                    "positioning: revenue recovery | CTA: Book demo | onboarding: import billing data | "
                    "source: https://rivaltwo.com/pricing | retrieved: 2026-05-15\n"
                    "Competitor: RivalThree | domain: rivalthree.com | pricing: custom | "
                    "positioning: retention workflows | CTA: View demo | onboarding: sample workspace | "
                    "source: https://rivalthree.com/pricing | retrieved: 2026-05-15\n"
                ),
            )
            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertTrue(result["recommendations_ready"])
            self.assertEqual(validate_insights_contract(insights, source_rows), [])
            self.assertTrue(insights["evidence_claims"])
            source_backed_claims = [claim for claim in insights["evidence_claims"] if claim["source_ids"]]
            self.assertGreaterEqual(len(source_backed_claims), 2)
            self.assertIn("pricing", {claim["claim_type"] for claim in source_backed_claims})
            self.assertIn("competitor", {claim["claim_type"] for claim in source_backed_claims})
            claim_by_id = {claim["claim_id"]: claim for claim in insights["evidence_claims"]}
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertTrue(recommendation["id"])
                self.assertTrue(recommendation["claim_ids"])
                self.assertTrue(recommendation["source_ids"] or recommendation["assumption_ids"])
                self.assertTrue(recommendation["owner_action"])
                self.assertTrue(recommendation["measurement_event"])
                if not recommendation["blocked_reason"]:
                    recommendation_sources = set(recommendation["source_ids"])
                    for claim_id in recommendation["claim_ids"]:
                        claim_sources = set(claim_by_id[claim_id]["source_ids"])
                        self.assertTrue(recommendation_sources & claim_sources)

    def test_launch_exports_are_outside_final_and_keep_contract_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "launch-exports"
            seed_rich_competitor_patterns(workspace)
            run_script("render_final.py", str(workspace), "--json")

            result = run_script("export_launch.py", str(workspace), "--json")

            self.assertTrue(result["ready_for_launch"])
            assert_launch_exports(workspace)
            action_plan = json.loads((workspace / "exports" / "action_plan.json").read_text(encoding="utf-8"))
            event_schema = json.loads((workspace / "exports" / "event_schema.json").read_text(encoding="utf-8"))
            content_brief = json.loads((workspace / "exports" / "content_brief.json").read_text(encoding="utf-8"))
            crm_handoff = json.loads((workspace / "exports" / "crm_handoff.json").read_text(encoding="utf-8"))
            funnel_diff = json.loads((workspace / "exports" / "funnel_diff.json").read_text(encoding="utf-8"))
            variant_bundles = json.loads((workspace / "exports" / "variant_bundles.json").read_text(encoding="utf-8"))
            experiment_card = json.loads((workspace / "exports" / "experiment_card.json").read_text(encoding="utf-8"))

            self.assertTrue(action_plan["ready_for_launch"])
            self.assertTrue(action_plan["items"])
            self.assertTrue(event_schema["events"])
            self.assertTrue(content_brief["briefs"])
            self.assertTrue(crm_handoff["handoffs"])
            self.assertTrue(funnel_diff["diffs"])
            self.assertTrue(variant_bundles["variants"])
            self.assertTrue(experiment_card["experiments"])
            for item in action_plan["items"]:
                self.assertTrue(item["claim_ids"])
                self.assertTrue(item["source_ids"])
                self.assertIn("assumption_ids", item)
                self.assertIn("blocked_reason", item)
            self.assertTrue(all(event["claim_ids"] for event in event_schema["events"]))
            self.assertTrue(all(event["source_ids"] for event in event_schema["events"]))
            self.assertTrue(all(item["claim_ids"] for item in funnel_diff["diffs"]))
            self.assertTrue(all(item["claim_ids"] for item in variant_bundles["variants"]))
            self.assertTrue(all(item["source_ids"] for item in variant_bundles["variants"]))
            self.assertTrue(experiment_card["experiments"][0]["event_id"])

    def test_orchestration_contract_exists_and_validates_for_ready_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "orchestration-ready"
            seed_rich_competitor_patterns(workspace)

            result = run_script("validate_workspace.py", str(workspace), "--json")
            contract = json.loads((workspace / "runtime" / "orchestration_contract.json").read_text(encoding="utf-8"))
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = read_source_rows(workspace)

            self.assertEqual(result["phase"], "ready")
            self.assertEqual(contract["contract_type"], "orchestration_task_results")
            self.assertEqual(validate_orchestration_contract(contract, insights, source_rows), [])
            self.assertTrue(contract["tasks"])
            required = {
                "task_id",
                "role",
                "specialist",
                "objective",
                "input_refs",
                "context_refs",
                "output_refs",
                "artifact_refs",
                "claim_ids",
                "source_ids",
                "assumption_ids",
                "blocked_reason",
                "status",
                "created_at",
                "updated_at",
            }
            for task in contract["tasks"]:
                self.assertTrue(required.issubset(task))
            synthesis = next(task for task in contract["tasks"] if task["role"] == "synthesis")
            self.assertIn("runtime/insights.json", synthesis["output_refs"])
            self.assertTrue(synthesis["claim_ids"])
            self.assertTrue(synthesis["source_ids"])

    def test_orchestration_contract_keeps_blocked_specialist_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "orchestration-blocked-specialist"
            run_script("create_workspace.py", "--name", "Blocked specialist", "--out", str(workspace), "--json")
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
            payload = {
                "role": "research",
                "topic_id": "research_evidence",
                "task_id": "research-1",
                "objective": "Check current-practice proof for activation audit claims.",
                "summary": "One public source was found; this remains research-only.",
                "key_findings": ["Need at least two more independent sources."],
                "citations": [{"url": "https://example.com/research", "title": "Research"}],
                "freshness_date": "2026-05-15",
                "confidence": "medium",
                "assumption_ids": ["A1"],
                "blocked_reason": "Need two more independent sources before synthesis can be ready.",
                "status": "blocked",
                "input_refs": ["runtime/intake.json"],
                "output_refs": ["runtime/sources.jsonl", "runtime/agent_results.jsonl"],
            }

            run_script("record_agent_result.py", str(workspace), "--input", "-", "--json", input_text=json.dumps(payload))
            contract = json.loads((workspace / "runtime" / "orchestration_contract.json").read_text(encoding="utf-8"))
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = read_source_rows(workspace)
            research_task = next(task for task in contract["tasks"] if task["task_id"] == "research-1")

            self.assertEqual(validate_orchestration_contract(contract, insights, source_rows), [])
            self.assertEqual(research_task["status"], "blocked")
            self.assertIn("Need two more independent sources", research_task["blocked_reason"])
            self.assertIn("A1", research_task["assumption_ids"])
            self.assertTrue(research_task["source_ids"])
            self.assertIn("runtime/sources.jsonl", research_task["output_refs"])

    def test_orchestration_contract_references_known_ids_and_stays_out_of_final(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "orchestration-final"
            seed_rich_competitor_patterns(workspace)

            run_script("render_final.py", str(workspace), "--json")
            contract = json.loads((workspace / "runtime" / "orchestration_contract.json").read_text(encoding="utf-8"))
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = read_source_rows(workspace)
            claim_ids = {claim["claim_id"] for claim in insights["evidence_claims"]}
            source_ids = {row["source_id"] for row in source_rows}
            assumption_ids = {row["id"] for row in insights["assumptions"]}

            self.assertEqual(validate_orchestration_contract(contract, insights, source_rows), [])
            for task in contract["tasks"]:
                self.assertTrue(set(task["claim_ids"]).issubset(claim_ids))
                self.assertTrue(set(task["source_ids"]).issubset(source_ids))
                self.assertTrue(set(task["assumption_ids"]).issubset(assumption_ids))
            combined_final = "\n".join(path.read_text(encoding="utf-8") for path in (workspace / "final").glob("*.md"))
            self.assertNotIn('"orchestration_contract"', combined_final)
            self.assertNotIn("orchestration_task_results", combined_final)
            assert_final_pack(workspace)

    def test_orchestration_contract_export_is_in_exports_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "orchestration-export"
            seed_rich_competitor_patterns(workspace)
            run_script("render_final.py", str(workspace), "--json")

            result = run_script("export_launch.py", str(workspace), "--json")
            payload = json.loads((workspace / "exports" / "orchestration_contract.json").read_text(encoding="utf-8"))
            manifest = json.loads((workspace / "exports" / "manifest.json").read_text(encoding="utf-8"))
            runtime_contract = json.loads((workspace / "runtime" / "orchestration_contract.json").read_text(encoding="utf-8"))

            self.assertTrue(result["ready_for_launch"])
            self.assertIn("orchestration_contract", manifest["exports"])
            self.assertTrue((workspace / "exports" / "orchestration_contract.csv").exists())
            self.assertEqual(payload["contract_type"], "orchestration_task_results")
            self.assertTrue(payload["tasks"])
            self.assertIn("exports/orchestration_contract.json", runtime_contract["export_refs"])
            assert_launch_exports(workspace)
            assert_final_pack(workspace)

    def test_launch_exports_remain_blocked_for_research_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "blocked-launch-exports"
            run_script("create_workspace.py", "--name", "Blocked exports", "--out", str(workspace), "--json")
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

            result = run_script("export_launch.py", str(workspace), "--json")

            self.assertFalse(result["ready_for_launch"])
            self.assertIn("evidence_gaps", result["blocked_reason"])
            assert_launch_exports(workspace)
            action_plan = json.loads((workspace / "exports" / "action_plan.json").read_text(encoding="utf-8"))
            variant_bundles = json.loads((workspace / "exports" / "variant_bundles.json").read_text(encoding="utf-8"))
            experiment_card = json.loads((workspace / "exports" / "experiment_card.json").read_text(encoding="utf-8"))
            self.assertFalse(action_plan["ready_for_launch"])
            self.assertTrue(action_plan["blocked_reason"])
            for item in action_plan["items"]:
                self.assertFalse(item["ready"])
                self.assertTrue(item["assumption_ids"])
                self.assertTrue(item["blocked_reason"])
            for item in variant_bundles["variants"]:
                self.assertFalse(item["ready"])
                self.assertTrue(item["assumption_ids"])
                self.assertTrue(item["blocked_reason"])
            for item in experiment_card["experiments"]:
                self.assertFalse(item["ready"])
                self.assertTrue(item["blocked_reason"])

    def test_current_funnel_diff_uses_provided_steps_in_runtime_final_and_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "current-funnel-diff"
            seed_rich_competitor_patterns(workspace)
            result = run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text="Current funnel: Search ad -> generic landing page -> signup form -> manual call\n",
            )

            self.assertIn("current_funnel", result["changed"]["intake"])
            run_script("render_final.py", str(workspace), "--json")
            export_result = run_script("export_launch.py", str(workspace), "--json")
            intake = json.loads((workspace / "runtime" / "intake.json").read_text(encoding="utf-8"))
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            diff = insights["current_funnel_diff"]
            blueprint = (workspace / "final" / "05_funnel_blueprint.md").read_text(encoding="utf-8")
            funnel_diff_export = json.loads((workspace / "exports" / "funnel_diff.json").read_text(encoding="utf-8"))

            self.assertTrue(export_result["ready_for_launch"])
            self.assertEqual(validate_insights_contract(insights, source_rows), [])
            self.assertEqual(intake["current_funnel"], ["Search ad", "generic landing page", "signup form", "manual call"])
            self.assertEqual(diff["status"], "provided")
            self.assertEqual(diff["raw_current_steps"], intake["current_funnel"])
            self.assertGreaterEqual(len(diff["rows"]), 4)
            self.assertIn("generic landing page", json.dumps(diff["rows"], ensure_ascii=False))
            self.assertIn("SearchIntentMatched", json.dumps(diff["rows"], ensure_ascii=False))
            self.assertTrue(all(row["claim_ids"] for row in diff["rows"]))
            self.assertIn("Current vs Proposed Changes", blueprint)
            self.assertIn("generic landing page", blueprint)
            self.assertIn("SearchIntentMatched", blueprint)
            self.assertNotIn('"current_funnel_diff"', blueprint)
            self.assertNotIn('"raw_current_steps"', blueprint)
            self.assertEqual(funnel_diff_export["status"], "provided")
            self.assertTrue(funnel_diff_export["diffs"])
            assert_markdown_row_columns(blueprint, "generic landing page", 6)
            assert_final_pack(workspace)

    def test_missing_current_funnel_is_visible_assumption_without_blocking_ready_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "missing-current-funnel"
            seed_rich_competitor_patterns(workspace)

            result = run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            diff = insights["current_funnel_diff"]
            blueprint = (workspace / "final" / "05_funnel_blueprint.md").read_text(encoding="utf-8")

            self.assertEqual(result["phase"], "ready")
            self.assertTrue(result["recommendations_ready"])
            self.assertEqual(validate_insights_contract(insights, source_rows), [])
            self.assertEqual(diff["status"], "missing_current_funnel")
            self.assertEqual(diff["raw_current_steps"], [])
            self.assertTrue(all(not row["current_step"] for row in diff["rows"]))
            self.assertTrue(any("A6" in row["assumption_ids"] for row in diff["rows"]))
            self.assertTrue(any(row["blocked_reason"] for row in diff["rows"]))
            self.assertIn("Current funnel was not provided", blueprint)
            self.assertIn("does not invent current steps", blueprint)
            self.assertNotIn('"current_funnel_diff"', blueprint)
            assert_final_pack(workspace)

    def test_current_funnel_diff_keeps_assumptions_and_blockers_in_research_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "draft-current-funnel"
            run_script("create_workspace.py", "--name", "Draft current funnel", "--out", str(workspace), "--json")
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
                    "Current funnel: LinkedIn post -> website form -> manual email follow-up\n"
                    "No proof yet\n"
                ),
            )

            result = run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            diff = insights["current_funnel_diff"]
            blueprint = (workspace / "final" / "05_funnel_blueprint.md").read_text(encoding="utf-8")

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertEqual(validate_insights_contract(insights, []), [])
            self.assertEqual(diff["status"], "provided")
            for row in diff["rows"]:
                self.assertTrue(row["assumption_ids"])
                self.assertTrue(row["blocked_reason"])
            self.assertIn("manual email follow-up", blueprint)
            self.assertNotIn('"rows"', blueprint)
            assert_final_pack(workspace)

    def test_variant_bundles_are_visible_in_runtime_final_and_exports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "variant-bundles-ready"
            seed_rich_competitor_patterns(workspace)
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text="Current funnel: Search ad -> generic landing page -> signup form -> manual call\n",
            )

            render_result = run_script("render_final.py", str(workspace), "--json")
            export_result = run_script("export_launch.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            variants = insights["variant_bundles"]
            screen_specs = (workspace / "final" / "06_screen_specs.md").read_text(encoding="utf-8")
            variant_export = json.loads((workspace / "exports" / "variant_bundles.json").read_text(encoding="utf-8"))

            self.assertEqual(render_result["phase"], "ready")
            self.assertTrue(export_result["ready_for_launch"])
            self.assertEqual(validate_insights_contract(insights, source_rows), [])
            self.assertGreaterEqual(len(variants), 2)
            self.assertLessEqual(len(variants), 3)
            for variant in variants:
                self.assertTrue(variant["variant_id"])
                self.assertTrue(variant["measurement_event"])
                self.assertTrue(variant["hypothesis"])
                self.assertTrue(variant["proof_requirement"])
                self.assertTrue(variant["claim_ids"])
                self.assertTrue(variant["source_ids"])
                self.assertFalse(variant["blocked_reason"])
                self.assertTrue(variant["variant_copy"] or variant["variant_action"])
            self.assertIn("Variant Bundles", screen_specs)
            self.assertIn("Search ad", screen_specs)
            self.assertIn("SearchIntentMatched", screen_specs)
            self.assertNotIn('"variant_bundles"', screen_specs)
            self.assertNotIn('"variant_id"', screen_specs)
            self.assertEqual(len(variant_export["variants"]), len(variants))
            self.assertTrue(all(item["claim_ids"] for item in variant_export["variants"]))
            self.assertTrue(all(item["source_ids"] for item in variant_export["variants"]))
            assert_markdown_row_columns(screen_specs, "variant-1", 8)
            assert_launch_exports(workspace)
            assert_final_pack(workspace)

    def test_variant_bundles_keep_blockers_for_no_proof_research(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "variant-bundles-no-proof"
            run_script("create_workspace.py", "--name", "No proof variants", "--out", str(workspace), "--json")
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
                    "Current funnel: LinkedIn post -> website form -> manual email follow-up\n"
                    "No proof yet\n"
                ),
            )

            render_result = run_script("render_final.py", str(workspace), "--json")
            result = run_script("export_launch.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            variants = insights["variant_bundles"]
            screen_specs = (workspace / "final" / "06_screen_specs.md").read_text(encoding="utf-8")
            variant_export = json.loads((workspace / "exports" / "variant_bundles.json").read_text(encoding="utf-8"))

            self.assertEqual(render_result["phase"], "research")
            self.assertEqual(result["summary"]["phase"], "research")
            self.assertFalse(result["ready_for_launch"])
            self.assertEqual(validate_insights_contract(insights, []), [])
            self.assertTrue(variants)
            for variant in variants:
                self.assertTrue(variant["assumption_ids"])
                self.assertTrue(variant["blocked_reason"])
            for item in variant_export["variants"]:
                self.assertFalse(item["ready"])
                self.assertTrue(item["assumption_ids"])
                self.assertTrue(item["blocked_reason"])
            self.assertIn("Variant Bundles", screen_specs)
            self.assertNotIn('"variant_bundles"', screen_specs)
            self.assertNotIn('"blocked_reason"', screen_specs)
            assert_launch_exports(workspace)
            assert_final_pack(workspace)

    def test_variant_bundles_use_channel_niche_and_current_funnel_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "variant-signals"
            seed_channel_workspace(workspace, "Telegram bot")
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text="Current funnel: Meta ad -> generic bot -> manual CRM follow-up\n",
            )

            run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            combined = json.dumps(insights["variant_bundles"], ensure_ascii=False)

            self.assertEqual(insights["channel_synthesis"]["primary_channel_pack"], "telegram")
            self.assertEqual(insights["niche_profile"]["profile_key"], "saas")
            self.assertIn("Telegram", combined)
            self.assertIn("SaaS", combined)
            self.assertIn("generic bot", combined)
            self.assertIn("TelegramBotStarted", combined)
            self.assertIn("route", {variant["variant_type"] for variant in insights["variant_bundles"]})
            assert_final_pack(workspace)

    def test_rich_competitor_rows_shape_recommendations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "competitor-patterns"
            seed_rich_competitor_patterns(workspace)

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            synthesis = insights["competitor_synthesis"]
            combined_recommendations = json.dumps(
                insights["screens"] + insights["experiments"] + insights["risks"],
                ensure_ascii=False,
            )

            self.assertTrue(result["recommendations_ready"])
            self.assertEqual(synthesis["status"], "observed")
            for field in ["primary_cta", "onboarding_pattern", "proof", "pricing", "observed_weaknesses"]:
                self.assertIn(field, synthesis["patterns"])
            for expected in ["Start free", "connect Stripe", "customer stories", "$29/mo", "slow setup", "differentiation"]:
                self.assertIn(expected, combined_recommendations)

    def test_empty_competitor_observations_do_not_fabricate_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "empty-competitor-observations"
            run_script("create_workspace.py", "--name", "Weak competitor synthesis", "--out", str(workspace), "--json")
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
                    "Competitor: RivalOne | source: https://rivalone.com/pricing | retrieved: 2026-05-15\n"
                    "Competitor: RivalTwo | source: https://rivaltwo.com/pricing | retrieved: 2026-05-15\n"
                    "Competitor: RivalThree | source: https://rivalthree.com/pricing | retrieved: 2026-05-15\n"
                ),
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            combined_recommendations = json.dumps(insights["screens"] + insights["experiments"], ensure_ascii=False)

            self.assertFalse(result["recommendations_ready"])
            self.assertEqual(insights["competitor_synthesis"]["status"], "insufficient_competitor_patterns")
            self.assertEqual(insights["competitor_synthesis"]["patterns"], {})
            self.assertFalse(any("competitor_pattern" in row for row in insights["screens"] + insights["experiments"]))
            for fabricated in ["Start free", "Book demo", "sample workspace", "customer stories", "$29/mo", "differentiation"]:
                self.assertNotIn(fabricated, combined_recommendations)

    def test_competitor_aware_ready_recommendations_keep_claim_source_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "competitor-claim-source-mapping"
            seed_rich_competitor_patterns(workspace)

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            claim_by_id = {claim["claim_id"]: claim for claim in insights["evidence_claims"]}

            self.assertTrue(result["recommendations_ready"])
            self.assertEqual(validate_insights_contract(insights, source_rows), [])
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertFalse(recommendation["blocked_reason"])
                recommendation_sources = set(recommendation["source_ids"])
                self.assertTrue(recommendation_sources)
                for claim_id in recommendation["claim_ids"]:
                    self.assertTrue(recommendation_sources & set(claim_by_id[claim_id]["source_ids"]))

    def test_competitor_patterns_stay_draft_with_weak_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "weak-competitor-evidence"
            seed_rich_competitor_patterns(workspace)
            write_sources(
                workspace,
                [
                    evidence_source(1, "rivalone.com", weight="low", confidence="low"),
                    evidence_source(2, "rivaltwo.com", weight="low", confidence="low"),
                    evidence_source(3, "rivalthree.com", weight="low", confidence="low"),
                ],
            )

            result = run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertIn("low-weight source cannot support recommendations", " ".join(result["evidence_gaps"]))
            self.assertEqual(insights["competitor_synthesis"]["status"], "observed")
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertTrue(recommendation["blocked_reason"])
            assert_final_pack(workspace)

    def test_final_competitor_page_renders_synthesis_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "competitor-render"
            seed_rich_competitor_patterns(workspace)

            run_script("render_final.py", str(workspace), "--json")
            page = (workspace / "final" / "04_competitor_map.md").read_text(encoding="utf-8")

            self.assertIn("Pattern Synthesis", page)
            self.assertIn("Source IDs", page)
            self.assertIn("competitor CTAs", page)
            self.assertIn("Start free", page)
            self.assertIn("Observed Weaknesses", page)
            self.assertIn("slow setup", page)
            self.assertNotIn('"patterns"', page)
            assert_final_pack(workspace)

    def test_weak_competitor_page_does_not_render_fabricated_synthesis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "weak-competitor-render"
            run_script("create_workspace.py", "--name", "Weak competitor render", "--out", str(workspace), "--json")
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
                    "Competitor: RivalOne | source: https://rivalone.com/pricing | retrieved: 2026-05-15\n"
                    "Competitor: RivalTwo | source: https://rivaltwo.com/pricing | retrieved: 2026-05-15\n"
                    "Competitor: RivalThree | source: https://rivalthree.com/pricing | retrieved: 2026-05-15\n"
                ),
            )

            run_script("render_final.py", str(workspace), "--json")
            page = (workspace / "final" / "04_competitor_map.md").read_text(encoding="utf-8")

            self.assertIn("Repeatable competitor patterns are not strong enough yet", page)
            for fabricated in ["Start free", "Book demo", "customer stories", "$29/mo"]:
                self.assertNotIn(fabricated, page)
            assert_final_pack(workspace)

    def test_required_channel_packs_change_recommendations_events_and_risks(self) -> None:
        cases = {
            "search": ("SearchIntentMatched", "keyword-to-promise", "Search differentiation test"),
            "Meta Ads": ("MetaCreativeClicked", "message prequalification", "Meta differentiation test"),
            "LinkedIn content": ("LinkedInTrustClicked", "expert proof", "LinkedIn differentiation test"),
            "Telegram bot": ("TelegramBotStarted", "intent scoring", "Telegram differentiation test"),
            "webinar": ("WebinarRegistered", "Q&A objections", "Webinar differentiation test"),
            "email nurture": ("EmailSegmentMatched", "lifecycle trigger", "Email differentiation test"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for channel, (event_id, expected_phrase, experiment_name) in cases.items():
                workspace = Path(tmp) / channel.lower().replace(" ", "-")
                seed_channel_workspace(workspace, channel)

                result = run_script("validate_workspace.py", str(workspace), "--json")
                insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
                combined = json.dumps(insights["screens"] + insights["experiments"] + insights["risks"], ensure_ascii=False)

                self.assertTrue(result["recommendations_ready"], channel)
                self.assertEqual(insights["channel_synthesis"]["status"], "matched")
                self.assertEqual(insights["screens"][0]["event_id"], event_id)
                self.assertIn(expected_phrase, combined)
                self.assertIn(experiment_name, combined)
                self.assertTrue(any(event_id in row.get("event_id", "") for row in insights["screens"]))

    def test_multi_channel_input_sets_primary_pack_and_support_loops(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "multi-channel"
            seed_channel_workspace(workspace, "Meta Ads, Telegram bot, webinar, CRM follow-up")

            run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            channel_synthesis = insights["channel_synthesis"]

            self.assertEqual(channel_synthesis["primary_channel_pack"], "meta")
            self.assertEqual([loop["channel"] for loop in channel_synthesis["support_loops"]], ["telegram", "webinar", "email"])
            self.assertEqual(insights["screens"][0]["event_id"], "MetaCreativeClicked")
            self.assertIn("Multi-channel handoff", json.dumps(insights["risks"], ensure_ascii=False))

    def test_final_report_renders_channel_route_without_raw_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "channel-render"
            seed_channel_workspace(workspace, "Meta Ads, Telegram bot, webinar, CRM follow-up")

            run_script("render_final.py", str(workspace), "--json")
            blueprint = (workspace / "final" / "05_funnel_blueprint.md").read_text(encoding="utf-8")
            tracking = (workspace / "final" / "07_tracking_plan.md").read_text(encoding="utf-8")
            html = (workspace / "final" / "05_funnel_blueprint.html").read_text(encoding="utf-8")
            combined = blueprint + tracking + html

            self.assertIn("## Channel Route", blueprint)
            self.assertIn("MetaCreativeClicked", combined)
            self.assertIn("TelegramBotStarted", combined)
            self.assertIn("WebinarRegistered", combined)
            self.assertIn("EmailSegmentMatched", combined)
            self.assertIn("Support loop", blueprint)
            self.assertNotIn("primary_channel_pack", combined)
            self.assertNotIn("support_loops", combined)
            self.assertNotIn('"packs"', combined)
            assert_markdown_row_columns(blueprint, "| Primary | Meta |", 5)
            assert_markdown_row_columns(blueprint, "| Support loop | Telegram |", 5)
            assert_final_pack(workspace)

    def test_russian_channel_output_keeps_event_ids_in_english(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "russian-channel"
            run_script("create_workspace.py", "--name", "Russian channel", "--out", str(workspace), "--language", "Russian", "--json")
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=(
                    "Оффер: аудит Telegram-бота для воронки вебинара\n"
                    "ICP: владельцы онлайн-школ\n"
                    "Целевой KPI: квалифицированные заявки на консультацию\n"
                    "Канал: Telegram bot, webinar, email\n"
                    "TTFV: 3\n"
                    "Доказательство: кейс показал рост доходимости до консультации\n"
                    "Competitor: CourseOne | domain: courseone.example | positioning: webinar-first education | pricing: $99 | "
                    "CTA: Join webinar | onboarding: Telegram quiz | proof: student stories | first value: quiz score | "
                    "weakness: no-show risk | source: https://courseone.example/webinar | retrieved: 2026-05-15\n"
                    "Competitor: CourseTwo | domain: coursetwo.example | positioning: bot-led qualification | pricing: $149 | "
                    "CTA: Start bot | onboarding: intent branch | proof: testimonials | first value: lesson preview | "
                    "weakness: weak CRM handoff | source: https://coursetwo.example/bot | retrieved: 2026-05-15\n"
                    "Competitor: CourseThree | domain: coursethree.example | positioning: consultation funnel | pricing: custom | "
                    "CTA: Book call | onboarding: webinar replay | proof: case study | first value: readiness checklist | "
                    "weakness: delayed follow-up | source: https://coursethree.example/call | retrieved: 2026-05-15\n"
                ),
            )

            run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            tracking = (workspace / "final" / "07_tracking_plan.md").read_text(encoding="utf-8")
            blueprint = (workspace / "final" / "05_funnel_blueprint.md").read_text(encoding="utf-8")

            self.assertEqual(insights["output_language"], "Russian")
            self.assertEqual(insights["channel_synthesis"]["primary_channel_pack"], "telegram")
            self.assertEqual(insights["screens"][0]["event_id"], "TelegramBotStarted")
            self.assertIn("TelegramBotStarted", tracking)
            self.assertIn("Метрики и события", tracking)
            self.assertIn("Канальный маршрут", blueprint)
            self.assertIn("поддерживающий цикл", blueprint)
            for forbidden in ["Primary channel pack", "support_loop", "guardrail", "journey", "Event IDs", "Source IDs", "CTA"]:
                self.assertNotIn(forbidden, blueprint + tracking)
            assert_final_pack(workspace)

    def test_niche_profiles_are_visible_and_shape_guidance(self) -> None:
        cases = {
            "saas": (
                "Offer: SaaS analytics dashboard that connects Stripe and CRM\n"
                "ICP: B2B SaaS founders and RevOps teams\n"
                "Target KPI: trial activation\n"
                "Channel: search\n"
                "No proof yet\n",
                "SaaS",
                "FirstValueReached",
                "activation",
            ),
            "real_estate": (
                "Offer: overseas real estate property shortlist and buyer consultation\n"
                "ICP: relocation buyers and lifestyle investors\n"
                "Target KPI: qualified consultation booked\n"
                "Channel: Meta Ads\n"
                "No proof yet\n",
                "Real Estate",
                "ShortlistPreviewViewed",
                "buyer",
            ),
            "education": (
                "Offer: cohort education program with lessons and assignments\n"
                "ICP: entrepreneurs joining a course\n"
                "Target KPI: strategy call qualified\n"
                "Channel: webinar\n"
                "No proof yet\n",
                "Education",
                "LessonPreviewViewed",
                "learning outcome",
            ),
            "marketplace": (
                "Offer: two-sided marketplace to match families with verified providers\n"
                "ICP: families submitting care requests\n"
                "Target KPI: matched consultation booked\n"
                "Channel: Google Search\n"
                "No proof yet\n",
                "Marketplace",
                "ShortlistDelivered",
                "supply",
            ),
            "local_services": (
                "Offer: dental clinic implant consultation appointment for local expats\n"
                "ICP: English-speaking patients near Barcelona\n"
                "Target KPI: appointment booked\n"
                "Channel: Google Search plus WhatsApp follow-up\n"
                "No proof yet\n",
                "Local Services",
                "AppointmentBooked",
                "appointment",
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            for expected_key, (notes, label, event_id, phrase) in cases.items():
                workspace = Path(tmp) / expected_key
                run_script("create_workspace.py", "--name", label, "--out", str(workspace), "--json")
                run_script("ingest_notes.py", str(workspace), "--input", "-", "--json", input_text=notes)

                run_script("render_final.py", str(workspace), "--json")
                insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
                profile = insights["niche_profile"]
                combined = json.dumps(insights["screens"] + insights["risks"] + [profile], ensure_ascii=False)
                segments = (workspace / "final" / "02_intake_brief.md").read_text(encoding="utf-8")
                tracking = (workspace / "final" / "07_tracking_plan.md").read_text(encoding="utf-8")

                self.assertEqual(profile["status"], "matched", expected_key)
                self.assertEqual(profile["profile_key"], expected_key)
                self.assertIn(label, segments)
                self.assertIn("Niche Profile", segments)
                self.assertIn(event_id, tracking)
                self.assertIn(phrase, combined)
                self.assertNotIn('"niche_profile"', segments + tracking)
                assert_final_pack(workspace)

    def test_channel_ready_recommendations_keep_claim_source_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "channel-mapping"
            seed_channel_workspace(workspace, "LinkedIn content")

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            claim_by_id = {claim["claim_id"]: claim for claim in insights["evidence_claims"]}

            self.assertTrue(result["recommendations_ready"])
            self.assertEqual(validate_insights_contract(insights, source_rows), [])
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertFalse(recommendation["blocked_reason"])
                recommendation_sources = set(recommendation["source_ids"])
                for claim_id in recommendation["claim_ids"]:
                    self.assertTrue(recommendation_sources & set(claim_by_id[claim_id]["source_ids"]))

    def test_experiment_quality_gates_are_structured_and_rendered(self) -> None:
        required_fields = [
            "event_id",
            "guardrail_metrics",
            "exposure_definition",
            "event_instrumentation",
            "srm_check",
            "event_loss_threshold",
            "expected_effect_range",
            "stop_rule",
            "ship_rule",
            "iterate_rule",
            "failure_mode",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "experiment-quality"
            seed_channel_workspace(workspace, "webinar")

            run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            experiment = insights["experiments"][0]
            page = (workspace / "final" / "08_experiment_card.md").read_text(encoding="utf-8")
            html = (workspace / "final" / "08_experiment_card.html").read_text(encoding="utf-8")

            for field in required_fields:
                self.assertTrue(experiment.get(field), field)
            self.assertEqual(experiment["measurement_event"], experiment["event_id"])
            self.assertEqual(experiment["event_id"], "PostWebinarDecisionRouted")
            self.assertIn("Experiment Quality Gates", page)
            self.assertIn("SRM check", page)
            self.assertIn("Event loss", page)
            self.assertIn("PostWebinarDecisionRouted", html)
            assert_markdown_row_columns(page, "Eligible traffic", 8)
            assert_final_pack(workspace)

    def test_low_traffic_experiment_uses_sequential_learning_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "low-traffic-experiment"
            seed_channel_workspace(workspace, "LinkedIn content")
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text="Metric: traffic 30 sessions last month\n",
            )

            run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            experiment = insights["experiments"][0]
            page = (workspace / "final" / "08_experiment_card.md").read_text(encoding="utf-8")

            self.assertIn("Traffic is too low for reliable SRM", experiment["srm_check"])
            self.assertIn("Do not claim statistical lift", experiment["expected_effect_range"])
            self.assertNotIn("+5-15%", experiment["expected_effect_range"])
            self.assertIn("Do not claim statistical lift", page)
            self.assertIn("guarded rollout", page)

    def test_experiment_contract_requires_measurable_event_and_quality_gates(self) -> None:
        source_rows = [
            {
                "source_id": "source-1",
                "url": "https://example.com/case",
                "title": "Example case",
                "publisher": "example.com",
                "retrieved_at": "2026-05-15",
                "source_type": "case_study",
                "freshness": "current",
                "confidence": "high",
                "evidence_weight": "high",
                "used_in": ["experiment"],
            }
        ]
        insights = {
            "version": "test",
            "evidence_refs": [{"id": "source-1", "title": "Example case", "url": "https://example.com/case"}],
            "evidence_claims": [
                {
                    "claim_id": "claim-1",
                    "claim_text": "Case source supports experiment.",
                    "claim_type": "proof",
                    "source_ids": ["source-1"],
                    "freshness_required": False,
                    "freshness_status": "current",
                    "relevance_score": 0.9,
                    "confidence": "high",
                    "used_in": ["experiment-1"],
                }
            ],
            "assumptions": [],
            "screens": [],
            "experiments": [
                {
                    "id": "experiment-1",
                    "type": "experiment",
                    "target_segment": "SaaS operators",
                    "funnel_stage": "Experiment",
                    "claim_ids": ["claim-1"],
                    "source_ids": ["source-1"],
                    "assumption_ids": [],
                    "confidence": "high",
                    "blocked_reason": "",
                    "owner_action": "Test first-value route.",
                    "measurement_event": "",
                    "name": "First-value route test",
                    "hypothesis": "If users see first value before the CTA, activation improves.",
                    "change": "Test the first-value route.",
                    "primary_metric": "Activation",
                    "guardrail_metrics": "lead quality",
                    "exposure_definition": "Eligible users at the tested step.",
                    "event_instrumentation": "Log experiment_id and variant_id.",
                    "srm_check": "Check split daily.",
                    "event_loss_threshold": "5%",
                    "expected_effect_range": "+5-15%",
                    "stop_rule": "Stop on SRM failure.",
                    "ship_rule": "Ship on clean lift.",
                    "iterate_rule": "Iterate on flat metric.",
                    "failure_mode": "Attribution noise.",
                }
            ],
        }

        errors = validate_insights_contract(insights, source_rows)
        self.assertIn("missing event_id", " ".join(errors))
        self.assertIn("has no measurable event", " ".join(errors))

    def test_channel_pack_stays_draft_with_weak_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "weak-channel-evidence"
            seed_channel_workspace(workspace, "Telegram bot")
            write_sources(
                workspace,
                [
                    evidence_source(1, "rivalone.com", weight="low", confidence="low"),
                    evidence_source(2, "rivaltwo.com", weight="low", confidence="low"),
                    evidence_source(3, "rivalthree.com", weight="low", confidence="low"),
                ],
            )

            result = run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertEqual(insights["channel_synthesis"]["primary_channel_pack"], "telegram")
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertTrue(recommendation["blocked_reason"])
            assert_final_pack(workspace)

    def test_low_weight_sources_do_not_make_workspace_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "low-weight-sources"
            seed_ready_intake_and_competitors(workspace)
            write_sources(
                workspace,
                [
                    evidence_source(1, "listicle-one.example", weight="low", confidence="low", source_type="other"),
                    evidence_source(2, "listicle-two.example", weight="low", confidence="low", source_type="other"),
                    evidence_source(3, "listicle-three.example", weight="low", confidence="low", source_type="other"),
                ],
            )

            result = run_script("render_final.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertLess(result["research_readiness_score"], 60)
            self.assertIn("low-weight source cannot support recommendations", " ".join(result["evidence_gaps"]))
            self.assertEqual(insights["evidence_quality"]["ready_threshold"], 60)
            self.assertIn("low-weight sources", " ".join(insights["evidence_quality"]["blockers"]))
            assert_final_pack(workspace)

    def test_independent_current_relevant_sources_raise_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "strong-sources"
            seed_ready_intake_and_competitors(workspace)
            write_sources(
                workspace,
                [
                    evidence_source(1, "rivalone.com", weight="high", confidence="high"),
                    evidence_source(2, "rivaltwo.com", weight="medium", confidence="medium"),
                    evidence_source(3, "rivalthree.com", weight="medium", confidence="medium"),
                ],
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))

            self.assertEqual(result["phase"], "ready")
            self.assertTrue(result["recommendations_ready"])
            self.assertGreaterEqual(result["research_readiness_score"], 60)
            self.assertEqual(result["evidence_gaps"], [])
            self.assertGreaterEqual(insights["evidence_quality"]["dimensions"]["independence"]["score"], 100)
            self.assertGreaterEqual(insights["evidence_quality"]["dimensions"]["claim_coverage"]["score"], 90)
            claim_by_id = {claim["claim_id"]: claim for claim in insights["evidence_claims"]}
            for recommendation in insights["screens"] + insights["experiments"]:
                recommendation_sources = set(recommendation["source_ids"])
                self.assertTrue(recommendation_sources)
                for claim_id in recommendation["claim_ids"]:
                    self.assertTrue(recommendation_sources & set(claim_by_id[claim_id]["source_ids"]))

    def test_stale_current_sensitive_sources_block_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "stale-sources"
            seed_ready_intake_and_competitors(workspace)
            write_sources(
                workspace,
                [
                    evidence_source(1, "rivalone.com", weight="high", confidence="high", freshness="stale", retrieved_at="2025-01-10"),
                    evidence_source(2, "rivaltwo.com", weight="medium", confidence="medium", freshness="current"),
                    evidence_source(3, "rivalthree.com", weight="medium", confidence="medium", freshness="current"),
                ],
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertIn("stale", " ".join(result["evidence_gaps"]).lower())
            self.assertIn("stale", " ".join(insights["evidence_quality"]["blockers"]).lower())

    def test_uncovered_recommendation_claims_reduce_readiness(self) -> None:
        sources = [
            evidence_source(1, "rivalone.com", weight="high", confidence="high"),
            evidence_source(2, "rivaltwo.com", weight="medium", confidence="medium"),
            evidence_source(3, "rivalthree.com", weight="medium", confidence="medium"),
        ]
        insights = {
            "version": "test",
            "evidence_refs": [
                {"id": row["source_id"], "title": row["title"], "url": row["url"]}
                for row in sources
            ],
            "evidence_claims": [
                {
                    "claim_id": "claim-1",
                    "claim_text": "Pricing pages support the recommendation.",
                    "claim_type": "pricing",
                    "source_ids": ["source-1"],
                    "freshness_required": True,
                    "freshness_status": "current",
                    "relevance_score": 0.9,
                    "confidence": "high",
                    "used_in": ["screen-1"],
                }
            ],
            "assumptions": [{"id": "A1", "statement": "Draft assumption", "used_in": "screen_playbook"}],
            "screens": [
                {
                    "id": "screen-1",
                    "type": "screen",
                    "target_segment": "SaaS operators",
                    "funnel_stage": "Entry",
                    "claim_ids": ["claim-1"],
                    "source_ids": ["source-2"],
                    "assumption_ids": [],
                    "confidence": "high",
                    "blocked_reason": "",
                    "owner_action": "Show Stripe connection and churn-risk preview.",
                    "measurement_event": "First Value Reached / Trial Started",
                    "content": "Show Stripe connection and churn-risk preview.",
                }
            ],
            "experiments": [],
        }

        contract_errors = validate_insights_contract(insights, sources)
        quality = semantic_evidence_quality({"sources": sources, "intake": {}, "state": {}}, insights, contract_errors, [])

        self.assertIn("not covered by recommendation source_ids", " ".join(contract_errors))
        self.assertLess(quality["score"], 60)
        self.assertIn("contract errors block ready state", " ".join(quality["blockers"]))

    def test_assumption_fallback_supports_draft_but_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "draft-contract"
            run_script("create_workspace.py", "--name", "Draft contract", "--out", str(workspace), "--json")
            result = run_script(
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
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))

            self.assertTrue(result["summary"]["minimum_gate_satisfied"])
            self.assertEqual(result["summary"]["phase"], "research")
            self.assertFalse(result["summary"]["recommendations_ready"])
            self.assertEqual(validate_insights_contract(insights, []), [])
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertEqual(recommendation["source_ids"], [])
                self.assertTrue(recommendation["assumption_ids"])
                self.assertTrue(recommendation["blocked_reason"])

    def test_low_confidence_claims_do_not_make_recommendations_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "low-confidence-claims"
            seed_ready_intake_and_competitors(workspace)
            write_sources(
                workspace,
                [
                    evidence_source(1, "rivalone.com", weight="high", confidence="low"),
                    evidence_source(2, "rivaltwo.com", weight="medium", confidence="low"),
                    evidence_source(3, "rivalthree.com", weight="medium", confidence="low"),
                ],
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertIn("low confidence", " ".join(result["evidence_gaps"]))
            self.assertTrue(any(claim["confidence"] == "low" for claim in insights["evidence_claims"] if claim["source_ids"]))
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertTrue(recommendation["blocked_reason"])

    def test_insights_contract_rejects_unsupported_recommendations(self) -> None:
        source_rows = [
            {
                "source_id": "source-1",
                "url": "https://example.com/pricing",
                "title": "Example pricing",
                "publisher": "example.com",
                "retrieved_at": "2026-05-15",
                "source_type": "pricing",
                "freshness": "current",
                "confidence": "medium",
                "used_in": ["screen_playbook"],
            }
        ]
        base = {
            "version": "test",
            "evidence_refs": [{"id": "source-1", "title": "Example pricing", "url": "https://example.com/pricing"}],
            "evidence_claims": [
                {
                    "claim_id": "claim-1",
                    "claim_text": "Pricing page supports the recommendation.",
                    "claim_type": "pricing",
                    "source_ids": ["source-1"],
                    "freshness_required": True,
                    "freshness_status": "current",
                    "relevance_score": 0.8,
                    "confidence": "medium",
                    "used_in": ["screen-1"],
                }
            ],
            "assumptions": [{"id": "A1", "statement": "Draft assumption", "used_in": "screen_playbook"}],
            "screens": [
                {
                    "id": "screen-1",
                    "type": "screen",
                    "target_segment": "SaaS operators",
                    "funnel_stage": "Entry",
                    "claim_ids": ["claim-1"],
                    "source_ids": ["source-1"],
                    "assumption_ids": [],
                    "confidence": "medium",
                    "blocked_reason": "",
                    "owner_action": "Show Stripe connection and churn-risk preview.",
                    "measurement_event": "First Value Reached / Trial Started",
                    "content": "Show Stripe connection and churn-risk preview.",
                }
            ],
            "experiments": [],
        }

        self.assertEqual(validate_insights_contract(base, source_rows), [])

        missing_claims = json.loads(json.dumps(base))
        missing_claims["screens"][0]["claim_ids"] = []
        self.assertIn("has no claim_ids", " ".join(validate_insights_contract(missing_claims, source_rows)))

        unsupported = json.loads(json.dumps(base))
        unsupported["screens"][0]["source_ids"] = []
        unsupported["screens"][0]["assumption_ids"] = []
        self.assertIn("has no source_ids or assumption_ids", " ".join(validate_insights_contract(unsupported, source_rows)))

        unknown_source = json.loads(json.dumps(base))
        unknown_source["screens"][0]["source_ids"] = ["missing-source"]
        self.assertIn("unknown source_id missing-source", " ".join(validate_insights_contract(unknown_source, source_rows)))

        stale_source_rows = [dict(source_rows[0], retrieved_at="")]
        self.assertIn("stale current-sensitive source_id source-1", " ".join(validate_insights_contract(base, stale_source_rows)))

        low_weight_rows = [dict(source_rows[0], evidence_weight="low")]
        self.assertIn("low-weight source_id source-1", " ".join(validate_insights_contract(base, low_weight_rows)))

        low_confidence_claim = json.loads(json.dumps(base))
        low_confidence_claim["evidence_claims"][0]["confidence"] = "low"
        self.assertIn("evidence claim claim-1 has low confidence", " ".join(validate_insights_contract(low_confidence_claim, source_rows)))

        generic = json.loads(json.dumps(base))
        generic["screens"][0]["source_ids"] = []
        generic["screens"][0]["assumption_ids"] = ["A1"]
        generic["screens"][0]["owner_action"] = "Improve conversion"
        generic["screens"][0]["content"] = "Improve conversion"
        generic["screens"][0]["measurement_event"] = "conversion"
        self.assertIn("too generic or unsupported", " ".join(validate_insights_contract(generic, source_rows)))

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
            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertLessEqual(len(result["next_best_input"]), 2)

    def test_promise_proof_model_blocks_no_proof_ready_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "no-proof-with-sources"
            seed_promise_workspace(
                workspace,
                offer="connect Stripe and see churn risks in 3 minutes",
                proof_line="No proof yet",
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            model = insights["promise_proof_model"][0]

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertEqual(model["evidence_status"], "no_proof")
            self.assertTrue(model["assumption_ids"])
            self.assertIn("result promise has no proof yet", model["blocked_reason"])
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertIn("result promise has no proof yet", recommendation["blocked_reason"])

    def test_proof_mechanics_guidance_does_not_unblock_missing_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "proof-mechanics"
            seed_promise_workspace(
                workspace,
                offer="connect Stripe and see churn risks in 3 minutes",
                proof_line="No proof yet",
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            model = insights["promise_proof_model"][0]
            mechanic = model["recommended_proof_mechanic"]

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertEqual(model["evidence_status"], "no_proof")
            self.assertEqual(mechanic["claim_type"], "performance_outcome")
            self.assertEqual(mechanic["sales_motion"], "self_serve")
            self.assertEqual(mechanic["risk_level"], "medium")
            self.assertTrue(mechanic["guidance_only"])
            self.assertIn("Recommended proof format", model["proof_requirement"])
            self.assertIn("guidance only", mechanic["note"])
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertTrue(recommendation["blocked_reason"])
            self.assertTrue(any("Recommended proof format" in screen["proof_needed"] for screen in insights["screens"]))

    def test_promise_proof_model_blocks_weak_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "weak-proof"
            seed_promise_workspace(
                workspace,
                offer="connect Stripe and see churn risks in 3 minutes",
                proof_line="Proof: weak testimonial https://case.example/proof retrieved 2026-05-15",
            )
            write_sources(
                workspace,
                [
                    evidence_source(1, "case.example", weight="low", confidence="low", source_type="case_study"),
                    evidence_source(2, "rivalone.com", weight="high", confidence="high"),
                    evidence_source(3, "rivaltwo.com", weight="medium", confidence="medium"),
                    evidence_source(4, "rivalthree.com", weight="medium", confidence="medium"),
                ],
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            model = insights["promise_proof_model"][0]

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertEqual(model["evidence_status"], "weak_proof")
            self.assertEqual(model["source_ids"], ["source-1"])
            self.assertIn("proof is weak", model["blocked_reason"])

    def test_promise_proof_model_accepts_source_backed_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "source-backed-proof"
            seed_promise_workspace(
                workspace,
                offer="connect Stripe and see churn risks in 3 minutes",
                proof_line="Proof: customer case https://case.example/proof retrieved 2026-05-15",
            )
            write_sources(
                workspace,
                [
                    evidence_source(1, "case.example", weight="high", confidence="high", source_type="case_study"),
                    evidence_source(2, "rivalone.com", weight="high", confidence="high"),
                    evidence_source(3, "rivaltwo.com", weight="medium", confidence="medium"),
                    evidence_source(4, "rivalthree.com", weight="medium", confidence="medium"),
                ],
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            model = insights["promise_proof_model"][0]

            self.assertEqual(result["phase"], "ready")
            self.assertTrue(result["recommendations_ready"])
            self.assertEqual(model["evidence_status"], "source_backed")
            self.assertEqual(model["source_ids"], ["source-1"])
            self.assertTrue(model["claim_ids"])
            self.assertEqual(insights["reviewer_approval"]["status"], "not_required")
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertFalse(recommendation["blocked_reason"])

    def test_high_risk_source_backed_claim_requires_reviewer_approval_before_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "high-risk-review-required"
            seed_promise_workspace(
                workspace,
                offer="reduce revenue risk and legal exposure for SaaS teams",
                proof_line="Proof: customer case https://case.example/legal-revenue retrieved 2026-05-15",
                channel="LinkedIn content",
            )
            write_sources(
                workspace,
                [
                    evidence_source(1, "case.example", weight="high", confidence="high", source_type="case_study"),
                    evidence_source(2, "rivalone.com", weight="high", confidence="high"),
                    evidence_source(3, "rivaltwo.com", weight="medium", confidence="medium"),
                    evidence_source(4, "rivalthree.com", weight="medium", confidence="medium"),
                ],
            )

            result = run_script("render_final.py", str(workspace), "--json")
            export_result = run_script("export_launch.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            approval = insights["reviewer_approval"]
            page = (workspace / "final" / "01_status_next_steps.md").read_text(encoding="utf-8")
            approval_export = json.loads((workspace / "exports" / "reviewer_approval.json").read_text(encoding="utf-8"))

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertFalse(export_result["ready_for_launch"])
            self.assertEqual(validate_insights_contract(insights, source_rows), [])
            self.assertEqual(insights["promise_proof_model"][0]["risk_level"], "high")
            self.assertEqual(insights["promise_proof_model"][0]["evidence_status"], "source_backed")
            self.assertEqual(approval["status"], "required")
            self.assertTrue(approval["required"])
            self.assertFalse(approval["approved"])
            self.assertTrue(approval["review_items"])
            self.assertIn("reviewer approval", " ".join(result["evidence_gaps"]))
            self.assertIn("Reviewer Approval", page)
            self.assertIn("approval required", page)
            self.assertNotIn('"reviewer_approval"', page)
            self.assertEqual(approval_export["status"], "required")
            self.assertTrue(approval_export["review_items"])
            assert_launch_exports(workspace)
            assert_final_pack(workspace)

    def test_reviewer_approval_unblocks_high_risk_source_backed_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "high-risk-review-approved"
            seed_promise_workspace(
                workspace,
                offer="reduce revenue risk and legal exposure for SaaS teams",
                proof_line="Proof: customer case https://case.example/legal-revenue retrieved 2026-05-15",
                channel="LinkedIn content",
            )
            write_sources(
                workspace,
                [
                    evidence_source(1, "case.example", weight="high", confidence="high", source_type="case_study"),
                    evidence_source(2, "rivalone.com", weight="high", confidence="high"),
                    evidence_source(3, "rivaltwo.com", weight="medium", confidence="medium"),
                    evidence_source(4, "rivalthree.com", weight="medium", confidence="medium"),
                ],
            )
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text="Reviewer approval: approved by Growth Lead on 2026-05-17\n",
            )

            result = run_script("render_final.py", str(workspace), "--json")
            export_result = run_script("export_launch.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            approval = insights["reviewer_approval"]
            approval_export = json.loads((workspace / "exports" / "reviewer_approval.json").read_text(encoding="utf-8"))

            self.assertEqual(result["phase"], "ready")
            self.assertTrue(result["recommendations_ready"])
            self.assertTrue(export_result["ready_for_launch"])
            self.assertEqual(validate_insights_contract(insights, source_rows), [])
            self.assertEqual(approval["status"], "approved")
            self.assertTrue(approval["approved"])
            self.assertEqual(approval["approved_by"], "Growth Lead")
            self.assertEqual(approval["approved_at"], "2026-05-17")
            self.assertEqual(approval_export["status"], "approved")
            self.assertTrue(approval_export["approved"])
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertFalse(recommendation["blocked_reason"])

    def test_risky_claims_require_source_backed_proof(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "risky-proof"
            seed_promise_workspace(
                workspace,
                offer="guaranteed 30% investment return for relocation buyers",
                proof_line="Proof: founder anecdote",
                channel="Meta Ads",
            )

            result = run_script("validate_workspace.py", str(workspace), "--json")
            insights = json.loads((workspace / "runtime" / "insights.json").read_text(encoding="utf-8"))
            model = insights["promise_proof_model"][0]

            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertEqual(model["risk_level"], "high")
            self.assertEqual(model["evidence_status"], "risky_unverified")
            self.assertIn("A5", model["assumption_ids"])
            self.assertIn("risky promise needs source-backed proof and review", model["blocked_reason"])
            for recommendation in insights["screens"] + insights["experiments"]:
                self.assertIn("risky promise needs source-backed proof and review", recommendation["blocked_reason"])

    def test_russian_output_localizes_terms_and_blocks_empty_competitor_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ru-no-competitors"
            run_script(
                "create_workspace.py",
                "--name",
                "Зарубежная недвижимость",
                "--out",
                str(workspace),
                "--language",
                "Russian",
                "--json",
            )
            run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=(
                    "Оффер: подбор зарубежной недвижимости и консультация с продажником\n"
                    "Аудитория: русскоязычные покупатели недвижимости за рубежом\n"
                    "Метрика: квалифицированные лиды с телефоном, дошедшие до звонка\n"
                    "Канал: Facebook и Instagram реклама, Telegram bot, email\n"
                    "Нет доказательств пока\n"
                    "Источник: https://example.com/source-one 2026-05-15\n"
                    "Источник: https://example.com/source-two 2026-05-15\n"
                    "Источник: https://example.com/source-three 2026-05-15\n"
                    "Источник: https://example.com/source-four 2026-05-15\n"
                ),
            )
            result = run_script("render_final.py", str(workspace), "--json")

            self.assertTrue(result["minimum_gate_satisfied"])
            self.assertEqual(result["phase"], "research")
            self.assertFalse(result["recommendations_ready"])
            self.assertIn("карта конкурентов содержит меньше 3 конкурентов", result["evidence_gaps"])

            index = (workspace / "final" / "00_index.md").read_text(encoding="utf-8")
            execution = (workspace / "final" / "10_execution_plan.md").read_text(encoding="utf-8")
            blueprint = (workspace / "final" / "05_funnel_blueprint.md").read_text(encoding="utf-8")
            tracking = (workspace / "final" / "07_tracking_plan.md").read_text(encoding="utf-8")
            html_index = (workspace / "final" / "index.html").read_text(encoding="utf-8")

            self.assertIn("Пайплайн запуска", index)
            self.assertIn("Что сделать", index)
            self.assertIn("Зачем", index)
            self.assertIn("Что получишь", index)
            self.assertIn("Пайплайн запуска", execution)
            self.assertIn("Действие пользователя", blueprint)
            self.assertIn("Контрольный риск", tracking)
            self.assertIn("Пайплайн запуска", html_index)
            final_index_path = workspace.resolve() / "final" / "index.html"
            self.assertEqual(result["final_index_chat_link"], f"[Открыть финальный HTML]({final_index_path})")

            combined = "\n".join([index, execution, blueprint, tracking])
            self.assertNotIn("CTA", combined)
            self.assertNotIn("Guardrail", combined)
            self.assertNotIn("KPI Contract", combined)
            self.assertNotIn("skeleton", combined.lower())
            self.assertNotIn("support", combined.lower())

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
            self.assertFalse(summary["recommendations_ready"])
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

    def test_competitor_rows_need_observed_fields_not_only_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "weak-competitors"
            run_script("create_workspace.py", "--name", "Weak competitors", "--out", str(workspace), "--json")
            result = run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--kind",
                "competitor",
                "--json",
                input_text=(
                    "Competitor: RivalOne | source: https://rivalone.com | retrieved: 2026-05-17\n"
                    "Competitor: RivalTwo | source: https://rivaltwo.com | retrieved: 2026-05-17\n"
                    "Competitor: RivalThree | source: https://rivalthree.com | retrieved: 2026-05-17\n"
                ),
            )

            self.assertEqual(result["summary"]["competitor_count"], 3)
            self.assertIn("competitor row missing observed positioning/pricing/CTA/onboarding/proof", " ".join(result["summary"]["evidence_gaps"]))
            self.assertFalse(result["summary"]["recommendations_ready"])

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

    def test_research_web_parses_fixture_and_filters_low_weight_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "web-research"
            fixture = Path(tmp) / "search.html"
            fixture.write_text(
                """
                <html><body>
                  <a class="result__a" href="/l/?uddg=https%3A%2F%2Fexample.com%2Fpricing">Example Pricing</a>
                  <div class="result__snippet">Official pricing and plan limits for Example.</div>
                  <a class="result__a" href="https://content.example/top-10-tools">Top 10 AI tools</a>
                  <div class="result__snippet">A generic best tools list with no primary evidence.</div>
                  <a class="result__a" href="https://www.forbes.com/advisor/business/services/example-pricing/">Example Pricing Guide</a>
                  <div class="result__snippet">Secondary pricing summary for Example.</div>
                  <a class="result__a" href="https://g2.com/products/example/reviews">Example Reviews</a>
                  <div class="result__snippet">Customer review language and objections.</div>
                </body></html>
                """,
                encoding="utf-8",
            )
            run_script("create_workspace.py", "--name", "Web research", "--out", str(workspace), "--json")
            result = run_script(
                "research_web.py",
                str(workspace),
                "--query",
                "example pricing official",
                "--html-input",
                str(fixture),
                "--json",
            )

            self.assertEqual(result["changed"]["source_rows_added"], 3)
            self.assertEqual(result["accepted_count"], 3)
            self.assertEqual(result["rejected_count"], 1)
            source_rows = [
                json.loads(line)
                for line in (workspace / "runtime" / "sources.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(source_rows[0]["url"], "https://example.com/pricing")
            self.assertEqual(source_rows[0]["source_type"], "pricing")
            self.assertEqual(source_rows[0]["evidence_weight"], "high")
            self.assertEqual(source_rows[1]["source_type"], "pricing")
            self.assertEqual(source_rows[1]["evidence_weight"], "medium")
            self.assertEqual(source_rows[2]["source_type"], "review")
            self.assertEqual(source_rows[2]["evidence_weight"], "medium")
            self.assertTrue(source_rows[0]["retrieved_at"])
            self.assertEqual(len({row["source_id"] for row in source_rows}), len(source_rows))

    def test_research_competitors_parses_pages_and_filters_non_competitors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "competitor-research"
            search = Path(tmp) / "search.html"
            pages = Path(tmp) / "pages"
            pages.mkdir()
            search.write_text(
                """
                <html><body>
                  <a class="result__a" href="/l/?uddg=https%3A%2F%2Frivalone.com%2Fpricing">RivalOne Pricing</a>
                  <div class="result__snippet">Official pricing for RivalOne churn analytics.</div>
                  <a class="result__a" href="https://content.example/top-10-churn-tools">Top 10 churn tools</a>
                  <div class="result__snippet">A generic list of best tools.</div>
                  <a class="result__a" href="https://g2.com/products/rivalone/reviews">RivalOne Reviews</a>
                  <div class="result__snippet">Review language and ratings.</div>
                </body></html>
                """,
                encoding="utf-8",
            )
            (pages / "rivalone.com.html").write_text(
                """
                <html>
                  <head>
                    <title>RivalOne Pricing</title>
                    <meta name="description" content="RivalOne is churn analytics for SaaS teams. Connect Stripe to see at-risk accounts.">
                  </head>
                  <body>
                    <button>Start free</button>
                    <p>Plans start at $49/mo.</p>
                    <p>Connect Stripe and open the retention dashboard.</p>
                    <p>Trusted by 500 SaaS teams.</p>
                  </body>
                </html>
                """,
                encoding="utf-8",
            )
            run_script("create_workspace.py", "--name", "Competitor research", "--out", str(workspace), "--json")
            result = run_script(
                "research_competitors.py",
                str(workspace),
                "--query",
                "churn analytics competitors",
                "--html-input",
                str(search),
                "--page-fixture-dir",
                str(pages),
                "--json",
            )

            self.assertEqual(result["changed"]["competitor_rows_added"], 1)
            self.assertEqual(result["changed"]["source_rows_added"], 1)
            self.assertEqual(len(result["accepted_competitors"]), 1)
            rejected_reasons = " ".join(item["reason"] for item in result["rejected_candidates"])
            self.assertIn("generic listicle", rejected_reasons)
            self.assertIn("review/community domain", rejected_reasons)

            competitor = result["accepted_competitors"][0]
            self.assertEqual(competitor["competitor"], "Rivalone")
            self.assertEqual(competitor["domain"], "rivalone.com")
            self.assertEqual(competitor["pricing"], "$49/mo")
            self.assertEqual(competitor["primary_cta"], "Start free")
            self.assertEqual(competitor["onboarding_pattern"], "connect Stripe or billing data")
            self.assertEqual(competitor["proof"], "testimonials or trust proof observed")
            self.assertEqual(competitor["first_value_path"], "dashboard or analytics view")

    def test_research_competitors_can_move_ready_workspace_to_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "ready-competitors"
            search = Path(tmp) / "search.html"
            pages = Path(tmp) / "pages"
            pages.mkdir()
            search.write_text(
                """
                <html><body>
                  <a class="result__a" href="https://rivalone.com/pricing">RivalOne Pricing</a>
                  <div class="result__snippet">Official pricing.</div>
                  <a class="result__a" href="https://rivaltwo.com/pricing">RivalTwo Pricing</a>
                  <div class="result__snippet">Official pricing.</div>
                  <a class="result__a" href="https://rivalthree.com/pricing">RivalThree Pricing</a>
                  <div class="result__snippet">Official pricing.</div>
                </body></html>
                """,
                encoding="utf-8",
            )
            page_template = """
                <html>
                  <head><title>{name} Pricing</title><meta name="description" content="{name} helps SaaS teams find churn risks."></head>
                  <body><button>{cta}</button><p>{price}</p><p>Connect Stripe and view the analytics dashboard.</p><p>Customer stories available.</p></body>
                </html>
            """
            fixtures = [
                ("rivalone.com.html", "RivalOne", "Start free", "$29/mo"),
                ("rivaltwo.com.html", "RivalTwo", "Book demo", "$49/mo"),
                ("rivalthree.com.html", "RivalThree", "Request demo", "Custom pricing"),
            ]
            for filename, name, cta, price in fixtures:
                (pages / filename).write_text(page_template.format(name=name, cta=cta, price=price), encoding="utf-8")

            run_script("create_workspace.py", "--name", "Ready competitors", "--out", str(workspace), "--json")
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
                ),
            )
            result = run_script(
                "research_competitors.py",
                str(workspace),
                "--query",
                "churn analytics competitors pricing official",
                "--html-input",
                str(search),
                "--page-fixture-dir",
                str(pages),
                "--max-competitors",
                "3",
                "--json",
            )

            self.assertEqual(result["changed"]["competitor_rows_added"], 3)
            self.assertEqual(result["summary"]["competitor_count"], 3)
            self.assertEqual(result["summary"]["phase"], "ready")
            self.assertTrue(result["summary"]["recommendations_ready"])
            self.assertEqual(result["summary"]["evidence_gaps"], [])

    def test_research_competitors_rejects_candidates_without_observed_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "weak-competitor-pages"
            search = Path(tmp) / "search.html"
            pages = Path(tmp) / "pages"
            pages.mkdir()
            search.write_text(
                """
                <html><body>
                  <a class="result__a" href="https://rivalone.com/">RivalOne</a>
                  <a class="result__a" href="https://rivaltwo.com/">RivalTwo</a>
                  <a class="result__a" href="https://rivalthree.com/">RivalThree</a>
                </body></html>
                """,
                encoding="utf-8",
            )
            for domain in ["rivalone.com", "rivaltwo.com", "rivalthree.com"]:
                (pages / f"{domain}.html").write_text("<html><head><title>Welcome</title></head><body>Hello.</body></html>", encoding="utf-8")

            run_script("create_workspace.py", "--name", "Weak competitor pages", "--out", str(workspace), "--json")
            result = run_script(
                "research_competitors.py",
                str(workspace),
                "--query",
                "churn analytics competitors",
                "--html-input",
                str(search),
                "--page-fixture-dir",
                str(pages),
                "--json",
            )

            self.assertEqual(result["changed"]["competitor_rows_added"], 0)
            self.assertEqual(result["accepted_competitors"], [])
            self.assertIn("no observed competitor fields found", " ".join(item["reason"] for item in result["rejected_candidates"]))
            self.assertFalse(result["summary"]["recommendations_ready"])

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
            self.assertIn("С чего начать", final_index)
            self.assertIn("Главное решение", final_index)
            status = (workspace / "final" / "01_status_next_steps.md").read_text(encoding="utf-8")
            self.assertIn("Резюме решения", status)
            self.assertIn("Готовность данных", status)
            html = (workspace / "final" / "index.html").read_text(encoding="utf-8")
            self.assertIn("<title>Оглавление</title>", html)
            self.assertIn('<html lang="ru">', html)
            self.assertIn("index-grid", html)
            self.assertIn("Начать", html)
            page_html = (workspace / "final" / "00_index.html").read_text(encoding="utf-8")
            self.assertIn('<html lang="ru">', page_html)
            for forbidden in ["Intake brief", "Research и evidence", "Previous", "Next", "Auto-collect"]:
                self.assertNotIn(forbidden, final_index + status + html + page_html)

    def test_russian_ingest_updates_default_english_workspace_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "russian-default"
            created = run_script(
                "create_workspace.py",
                "--name",
                "Russian default",
                "--out",
                str(workspace),
                "--json",
            )
            self.assertEqual(created["output_language"], "English")
            result = run_script(
                "ingest_notes.py",
                str(workspace),
                "--input",
                "-",
                "--json",
                input_text=(
                    "Оффер: аудит Telegram-бота\n"
                    "ICP: владельцы онлайн-школ\n"
                    "Целевой KPI: завершение брифа\n"
                    "Канал: Telegram\n"
                    "Нет доказательств\n"
                ),
            )

            self.assertEqual(result["summary"]["output_language"], "Russian")
            intake = json.loads((workspace / "runtime" / "intake.json").read_text(encoding="utf-8"))
            self.assertEqual(intake["output_language"], "Russian")

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
