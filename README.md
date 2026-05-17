# Growth Funnel Skills

[![CI](https://github.com/saplq/growth-funnel-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/saplq/growth-funnel-skills/actions/workflows/ci.yml)

`designing-growth-funnels` is an Agent Skill that helps an AI agent build a practical, source-aware growth funnel package when enough business context, evidence, and measurable constraints are available.

It is designed for Codex, ChatGPT Skills, Claude Code, Claude.ai, and other agent hosts that support `SKILL.md`.

Repository: `saplq/growth-funnel-skills`

## Core Idea

Repeatable growth does not come from "creative marketing genius." It comes from a system that rejects weak cases early, turns vague goals into measurable KPI contracts, gives users fast first value, instruments each step, and improves through experiments.

This skill does **not** promise 90%+ success for every product, audience, and traffic source. It helps an agent produce a clearer, more testable, more evidence-aware funnel package.

```text
Fit Gate -> KPI Contract -> Journey Map -> First Value -> Instrumentation -> Experiment Loop -> Retention Loop -> Postmortem Library
```

## What It Produces

The final output is a human-readable decision package in `final/`:

| Area | Output |
| --- | --- |
| Decision | summary, first action, blockers, readiness |
| Audience | segments, jobs, objections, proof needs |
| Research | source-aware notes, assumptions, evidence gaps |
| Funnel | journey map, screen / bot / webinar / onboarding playbook, copy/action variants |
| Measurement | KPI contract, event tracking, guardrails |
| Experiment | first experiment card, decision rule, postmortem loop |
| Execution | risks, constraints, next steps |

When explicitly exported, machine-readable launch handoff files are written to `exports/`, not `final/`.

## Good Fit

The skill is broadly **segment-agnostic, but not context-agnostic**.

It can support SaaS, subscriptions, marketplaces, education, real estate, services, creator products, e-commerce, local businesses, Telegram/WhatsApp bots, webinars, onboarding, lead qualification, activation, and assisted-sales funnels.

It works best when the business has:

- a clear offer;
- a specific audience or primary persona;
- one target KPI;
- a primary channel;
- proof assets or explicit `no proof yet`;
- enough market context to research, measure, and test the path.

If those inputs are missing, the skill should produce a diagnosis and missing-data list, not a confident final strategy.

## Not A Fit

This skill should not be treated as:

- a magic growth strategy generator;
- a replacement for marketer judgment;
- proof that a funnel will convert;
- a source of invented metrics, proof, pricing, benchmarks, or customer claims;
- an automation that writes to CRM, ad accounts, analytics, messengers, or external systems without explicit approval.

## Install

Skills are installed into an agent host, not into a model name.

`skills/designing-growth-funnels/agents/openai.yaml` is OpenAI-specific UI metadata. It does not make the skill OpenAI-only. This repo does not include a separate `agents/claude.yaml`; hosts that support skills should read the skill contract from `SKILL.md`.

<details open>
<summary><strong>Codex</strong></summary>

Recommended:

```bash
npx skills add saplq/growth-funnel-skills --skill designing-growth-funnels
```

If you already installed an older version:

```bash
rm -rf ~/.codex/skills/designing-growth-funnels
npx skills add saplq/growth-funnel-skills --skill designing-growth-funnels
```

Local installer from a cloned repo:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
cd growth-funnel-skills
python3 scripts/install_skill.py codex --force
```

</details>

<details>
<summary><strong>ChatGPT Skills</strong></summary>

Create an uploadable zip:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
cd growth-funnel-skills
python3 scripts/install_skill.py zip --force
```

Upload `dist/designing-growth-funnels.zip` through the Skills upload flow available in your ChatGPT workspace. The exact UI labels can vary by plan and workspace settings.

Skills availability depends on your ChatGPT plan/workspace settings.

</details>

<details>
<summary><strong>Claude Code</strong></summary>

Personal install from a cloned repo:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
cd growth-funnel-skills
python3 scripts/install_skill.py claude --force
```

Manual personal install:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
mkdir -p ~/.claude/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels ~/.claude/skills/
```

Project-local install:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
mkdir -p .claude/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels .claude/skills/
```

Then start Claude Code in that environment and ask for the funnel.

</details>

<details>
<summary><strong>Claude.ai / Anthropic API</strong></summary>

Create a zip:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
cd growth-funnel-skills
python3 scripts/install_skill.py zip --force
```

Upload or attach `dist/designing-growth-funnels.zip` using the Skills workflow available in your Claude.ai plan or Anthropic API setup. The exact upload flow can vary by product surface.

</details>

<details>
<summary><strong>Other local agents</strong></summary>

If your agent reads `.agents/skills`:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
mkdir -p .agents/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels .agents/skills/
```

If your agent has another skills directory, copy `skills/designing-growth-funnels` into that directory.

</details>

## How To Use

After installation, write a normal business request. You do not need to mention scripts or runtime files.

```text
Use $designing-growth-funnels.

Build a marketing growth funnel and final report in English for this business.

Business:
[What the business sells]

Audience:
[Who the funnel is for]

Primary channel:
[Search, Meta Ads, LinkedIn, email, Telegram, webinars, partnerships, etc.]

Target KPI:
[The one metric the funnel should improve]

Current funnel:
[How people discover, evaluate, convert, and return today]

Current metrics:
[Any rough conversion rates, costs, revenue, activation, attendance, calls booked, etc.]

Proof:
[Case studies, testimonials, customers, usage, waitlist, sales, or write "no proof yet"]

Constraints:
[Budget, team, timeline, compliance, brand tone, tech limits]

Please create segmentation, funnel blueprint, screen or bot specs, tracking plan, first experiment card, risks, gaps, and next step.
```

More niche prompts are in [EXAMPLES.md](EXAMPLES.md).

## Expected Agent Behavior

1. Create a workspace.
2. Ingest the user context.
3. Validate whether the minimum funnel gate is complete.
4. Collect current sources when host web, browser, MCP, analytics, CRM, file, or local network tools are available; bundled collectors only cover best-effort public web and competitor discovery.
5. Compile `runtime/insights.json`.
6. Render `final/index.html`.
7. Reply first with a clickable Markdown link to `final/index.html`, then scores, blockers, and next step.

## Quality Model

The correct expectation is not "the skill always knows the answer."

The correct expectation is: **the skill makes the work structured, measurable, source-aware, and hard to fake.**

| Tier | Meaning |
| --- | --- |
| **Blocked** | Required business context is missing. |
| **Draft** | Core context exists, but sources, competitor evidence, proof, or metrics are limited. |
| **Ready to test** | Gate is complete, current sources and competitor evidence are recorded, KPI and tracking are defined, and the first experiment card is clear. |
| **Ready to execute carefully** | Owner, timeline, constraints, data, contradictions, and risks have been reviewed. |

## Methodology Basis

The skill is a practical growth operating model, not a scientific guarantee.

It combines:

- input gating and blocked-recommendation handling;
- audience segmentation and jobs-to-be-done thinking;
- KPI contracts and event-based measurement;
- funnel step design around user doubts, proof, and first value;
- source-aware competitor and current-practice research, with readiness blocked when evidence is weak or missing;
- assumption tracking, experiment planning, retention loops, and postmortems;
- clean final report generation from a separate runtime workspace.

Scientific references to predictive cognition, anticipation, uncertainty, and reward are used only as design analogies for sequencing attention, expectation, surprise, and resolution. They are not used as proof that a marketing funnel will work.

Freshness rule: the repository does not hardcode "latest market data" because that would become stale immediately. The skill expects the agent to gather fresh project-specific sources during each run when tools are available, and blocks readiness when current sources or retrieval dates are missing.

<details>
<summary><strong>Workspace and final pack</strong></summary>

The skill creates a workspace with two layers:

```text
funnel-workspace/
├── runtime/   # machine state, evidence, gaps, source registry, insights
├── final/     # user-facing Markdown and self-contained HTML
└── exports/   # optional machine-readable launch handoff JSON/CSV
```

`runtime/` is for the agent and audit trail, including `orchestration_contract.json` for task/result traceability. `final/` is for the user. `exports/` is created only by the launch export command and is for downstream implementation handoff.

The final pack contains:

```text
final/
├── index.html
├── 00_index.md / 00_index.html
├── 01_status_next_steps.md / .html
├── 02_intake_brief.md / .html
├── 03_research_evidence.md / .html
├── 04_competitor_map.md / .html
├── 05_funnel_blueprint.md / .html
├── 06_screen_specs.md / .html
├── 07_tracking_plan.md / .html
├── 08_experiment_card.md / .html
├── 09_risks_and_gaps.md / .html
└── 10_execution_plan.md / .html
```

</details>

<details>
<summary><strong>Manual CLI usage</strong></summary>

Most users should let the agent run scripts. Use these commands only for debugging or automation.

Create a workspace:

```bash
python3 skills/designing-growth-funnels/scripts/create_workspace.py \
  --name "Acme funnel" \
  --out ./workspaces/acme \
  --language "Russian" \
  --json
```

Ingest notes:

```bash
python3 skills/designing-growth-funnels/scripts/ingest_notes.py \
  ./workspaces/acme \
  --input ./notes/acme.txt \
  --kind notes \
  --json
```

Validate:

```bash
python3 skills/designing-growth-funnels/scripts/validate_workspace.py \
  ./workspaces/acme \
  --json
```

Optional best-effort public web discovery:

```bash
python3 skills/designing-growth-funnels/scripts/research_web.py \
  ./workspaces/acme \
  --query "focused current-practice query" \
  --json

python3 skills/designing-growth-funnels/scripts/research_competitors.py \
  ./workspaces/acme \
  --query "direct competitors pricing official" \
  --max-competitors 3 \
  --json
```

Render final output:

```bash
python3 skills/designing-growth-funnels/scripts/render_final.py \
  ./workspaces/acme \
  --json
```

Generate launch handoff exports outside `final/`:

```bash
python3 skills/designing-growth-funnels/scripts/export_launch.py \
  ./workspaces/acme \
  --json
```

The export command writes JSON and CSV files for `action_plan`, `event_schema`, `content_brief`, `crm_handoff`, `funnel_diff`, `variant_bundles`, `reviewer_approval`, `orchestration_contract`, and `experiment_card` into `exports/`. Draft or research-phase exports stay marked blocked and keep `claim_ids`, `source_ids`, `assumption_ids`, and `blocked_reason` visible.

</details>

## Development

Run tests:

```bash
python3 -m unittest discover -s tests
```

Compile-check scripts:

```bash
python3 -m compileall -q skills/designing-growth-funnels/scripts tests scripts
```

Package-check the upload zip:

```bash
python3 scripts/install_skill.py zip --force
```

Validate the skill metadata if your environment has the validator:

```bash
python3 /path/to/quick_validate.py skills/designing-growth-funnels
```

## Security

This skill is intentionally conservative:

- Python standard library only;
- network access only in explicitly run, read-only research collectors;
- no credential or environment secret reads;
- no execution of user-provided code;
- scripts write only inside the workspace path passed by the user;
- pasted notes and web pages are treated as data, not instructions.

See [SECURITY.md](SECURITY.md).

## License

MIT.
