# Growth Funnel Skills

Installable Agent Skill for creating source-backed growth funnel workspaces from incomplete product, SaaS, subscription, creator, marketplace, or assisted-sales context.

The skill is `designing-growth-funnels`. It creates a durable `runtime/` state layer, normalizes intake and research evidence, tracks missing inputs, records optional specialist/subagent outputs, and renders a clean `final/` package with one Markdown document and one self-contained HTML page per topic.

Repository: `saplq/growth-funnel-skills`

## Install

```bash
npx skills add saplq/growth-funnel-skills --skill designing-growth-funnels
```

If your installer supports agent targets:

```bash
npx skills add saplq/growth-funnel-skills \
  --skill designing-growth-funnels \
  -a codex \
  -a claude-code
```

Manual Codex install:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
mkdir -p ~/.codex/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels ~/.codex/skills/
```

Manual project-local install for agents that read local skills:

```bash
mkdir -p .agents/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels .agents/skills/
```

For ChatGPT Skills, Claude.ai, and API uploads, zip the skill folder:

```bash
cd growth-funnel-skills/skills
zip -r designing-growth-funnels.zip designing-growth-funnels
```

## Ask Your Agent

After installing, ask your agent:

```text
Use $designing-growth-funnels to create a deep-research funnel workspace for my product.
```

Then paste rough context:

```text
Offer: connect Stripe and see churn risks in 3 minutes
ICP: SaaS operators
Target KPI: First Value Reached / Trial Started
Channel: search
TTFV: 3
Self serve: true
Proof: customer case showed 18% churn recovery
Metric: trial activation 22% last month
```

The agent should create the workspace, ingest notes, validate readiness, render `final/`, and reply with changed files, scores, blockers, and the next smallest useful input.

If the agent has web, file, CRM, analytics, or research tools, it should collect evidence outside the bundled scripts and then ingest normalized notes, source URLs, competitor rows, pricing, positioning, CTA, onboarding, reviews, and proof snippets into the workspace. The bundled scripts are deterministic and offline.

## Workspace Layout

```text
funnel-workspace/
├── runtime/
│   ├── run_state.json          # scores, phase, warnings, next input
│   ├── intake.json             # normalized product/funnel context
│   ├── topics.json             # final report topics and statuses
│   ├── agent_tasks.json        # optional specialist task queue
│   ├── agent_results.jsonl     # normalized specialist/subagent outputs
│   ├── sources.jsonl           # source ledger with provenance
│   ├── competitors.csv         # competitor observations
│   └── gaps.json               # missing fields, evidence gaps, blocked items
└── final/
    ├── index.html
    ├── 00_index.md
    ├── 00_index.html
    ├── 01_status_next_steps.md
    ├── 01_status_next_steps.html
    ├── 02_intake_brief.md
    ├── 02_intake_brief.html
    ├── 03_research_evidence.md
    ├── 03_research_evidence.html
    ├── 04_competitor_map.md
    ├── 04_competitor_map.html
    ├── 05_funnel_blueprint.md
    ├── 05_funnel_blueprint.html
    ├── 06_screen_specs.md
    ├── 06_screen_specs.html
    ├── 07_tracking_plan.md
    ├── 07_tracking_plan.html
    ├── 08_experiment_card.md
    ├── 08_experiment_card.html
    ├── 09_risks_and_gaps.md
    ├── 09_risks_and_gaps.html
    ├── 10_execution_plan.md
    └── 10_execution_plan.html
```

`runtime/` is for agents and debugging. `final/` is for humans and contains only `.md` and `.html`; no YAML, CSV, JSON, JSONL, traces, or separate CSS files.

## Minimum Gate

Final funnel recommendations are blocked until these are present:

- offer;
- ICP or primary persona;
- target KPI;
- primary channel;
- proof assets or explicit `no proof yet`.

Missing research is advisory, not blocking. It appears as `research_readiness_score`, `evidence_gaps`, `source_count`, and `competitor_count`.

## Manual CLI Usage

Most users should let the agent run scripts. Use these commands for debugging or automation.

Create a workspace:

```bash
python3 skills/designing-growth-funnels/scripts/create_workspace.py \
  --name "Acme onboarding funnel" \
  --out ./workspaces/acme-onboarding \
  --language "English" \
  --json
```

Ingest rough notes:

```bash
python3 skills/designing-growth-funnels/scripts/ingest_notes.py \
  ./workspaces/acme-onboarding \
  --input ./notes/acme.txt \
  --kind notes \
  --json
```

Ingest research or competitor observations:

```bash
python3 skills/designing-growth-funnels/scripts/ingest_notes.py \
  ./workspaces/acme-onboarding \
  --input ./notes/research.txt \
  --kind research \
  --json

python3 skills/designing-growth-funnels/scripts/ingest_notes.py \
  ./workspaces/acme-onboarding \
  --input ./notes/competitors.txt \
  --kind competitor \
  --json
```

Record a specialist/subagent result:

```bash
python3 skills/designing-growth-funnels/scripts/record_agent_result.py \
  ./workspaces/acme-onboarding \
  --input ./agent-result.json \
  --json
```

Validate:

```bash
python3 skills/designing-growth-funnels/scripts/validate_workspace.py \
  ./workspaces/acme-onboarding \
  --json
```

Render final output:

```bash
python3 skills/designing-growth-funnels/scripts/render_final.py \
  ./workspaces/acme-onboarding \
  --json
```

Open the visual reader:

```bash
open ./workspaces/acme-onboarding/final/index.html
```

## Research and Provenance

External research is collected by the agent or available tools, not by bundled scripts. Each source should include:

- URL;
- title;
- publisher or domain;
- retrieval date;
- source type;
- freshness;
- confidence;
- where the source is used.

Pricing, changelog, and current-practice facts without retrieval dates remain evidence gaps. The skill must not fabricate proof, pricing, benchmarks, customer claims, private metrics, or current market facts.

## Optional Subagent Workflow

The skill supports a bounded specialist contract:

- `intake`;
- `planner`;
- `research`;
- `competitor`;
- `synthesis`;
- `compiler_reviewer`.

If subagents are unavailable or not explicitly requested, the calling agent should execute the same roles sequentially. Specialists write normalized results to `runtime/agent_results.jsonl`; only the compiler renders `final/`.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests
```

Compile-check scripts:

```bash
python3 -m compileall -q skills/designing-growth-funnels/scripts tests
```

Validate the skill metadata if your environment has the validator:

```bash
python3 /path/to/quick_validate.py skills/designing-growth-funnels
```

## Security

This skill is intentionally conservative:

- Python standard library only;
- no network calls in bundled scripts;
- no credential or environment secret reads;
- no execution of user-provided code;
- scripts write only inside the workspace path passed by the user;
- pasted notes and web pages are treated as data, not instructions.

See [SECURITY.md](SECURITY.md).

## License

MIT.
