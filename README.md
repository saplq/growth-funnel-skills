# Growth Funnel Skills

Installable Agent Skill for turning rough growth context into a structured funnel workspace.

The skill is `designing-growth-funnels`. It creates the project files, scores what is missing, asks for the next useful input, and renders a clean final pack with one Markdown document and one HTML page per topic.

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

<details>
<summary>OpenAI Codex</summary>

```bash
npx skills add saplq/growth-funnel-skills --skill designing-growth-funnels -a codex
```

Manual install:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
mkdir -p ~/.codex/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels ~/.codex/skills/
```

</details>

<details>
<summary>ChatGPT Skills</summary>

Create a zip and upload it through the ChatGPT Skills UI available in your account:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
cd growth-funnel-skills/skills
zip -r designing-growth-funnels.zip designing-growth-funnels
```

</details>

<details>
<summary>Claude Code</summary>

```bash
npx skills add saplq/growth-funnel-skills --skill designing-growth-funnels -a claude-code
```

Manual user-level install:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
mkdir -p ~/.claude/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels ~/.claude/skills/
```

Manual project-level install:

```bash
mkdir -p .claude/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels .claude/skills/
```

</details>

<details>
<summary>Claude.ai and Claude API</summary>

Create a zip and upload it through the Claude product or API flow available in your workspace:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
cd growth-funnel-skills/skills
zip -r designing-growth-funnels.zip designing-growth-funnels
```

</details>

<details>
<summary>Cursor, Windsurf, Gemini CLI, GitHub Copilot, OpenCode, and other agents</summary>

This repo follows the common Agent Skills folder shape: `SKILL.md` plus optional `references/`, `assets/`, and `scripts/`.

If your agent supports the skills CLI:

```bash
npx skills add saplq/growth-funnel-skills --skill designing-growth-funnels
```

If your agent supports project-local skills, copy the skill folder into its skills directory. A common fallback:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
mkdir -p .agents/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels .agents/skills/
```

Check your agent's docs for the exact folder. The requirement is simple: the agent must be able to read `SKILL.md`.

</details>

## Update An Installed Skill

The GitHub repo is the source of truth, but most agents install a local copy of the skill. That installed copy usually does not update itself when this repo changes.

To update, reinstall the skill:

```bash
npx skills add saplq/growth-funnel-skills --skill designing-growth-funnels
```

For manual installs, replace the old folder:

```bash
rm -rf ~/.codex/skills/designing-growth-funnels
cp -R growth-funnel-skills/skills/designing-growth-funnels ~/.codex/skills/
```

For ChatGPT, Claude.ai, and API uploads, create a fresh zip from the latest repo and upload it again. If your agent caches skills, restart or reload the agent after updating.

Existing workspaces are just files on disk. They will not automatically gain new output folders until the updated skill renders them again. For the clean reader-facing output, ask the agent to re-render the workspace and open `final/index.html`.

## Ask Your Agent

After installing, ask your agent to use the skill. You should not need to run the scripts manually.

```text
Use $designing-growth-funnels to create a funnel workspace for my product.
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

The agent should create the workspace, fill structured files, validate completeness, render the final pack, and tell you only what changed plus the next smallest input it needs.

Before the workspace is created, the agent should infer the language of your current conversation. Status files, questions, Markdown outputs, and the HTML presentation should be created in that language from the start unless you ask for a different language.

## What The Agent Creates

The workspace has two layers:

- root files for the agent and debugging;
- `final/` for the user-facing output.

```text
funnel-workspace/
├── 00_status.md              # scores, blockers, next input
├── 01_intake_brief.yaml      # offer, ICP, KPI, language, constraints
├── 02_proof_library.csv      # cases, testimonials, benchmarks, evidence
├── 03_current_metrics.csv    # baseline funnel metrics
├── 04_channel_context.yaml   # traffic source and message match
├── 05_segment_profile.yaml   # awareness, intent, tier, skeleton
├── 06_funnel_blueprint.md    # route, skeleton, assumptions
├── 07_screen_specs.md        # screen-by-screen belief shifts
├── 08_tracking_plan.csv      # events, properties, metrics, guardrails
├── 09_experiment_card.md     # hypothesis, KPI, decision rule
├── 10_postmortem_record.md   # learning archive template
├── 11_presentation.html      # compact workspace overview
└── final/
    ├── index.html
    ├── 00_index.md
    ├── 00_index.html
    ├── 01_status_next_steps.md
    ├── 01_status_next_steps.html
    ├── 02_funnel_blueprint.md
    ├── 02_funnel_blueprint.html
    ├── 03_screen_specs.md
    ├── 03_screen_specs.html
    ├── 04_tracking_plan.md
    ├── 04_tracking_plan.html
    ├── 05_experiment_card.md
    ├── 05_experiment_card.html
    ├── 06_postmortem_template.md
    └── 06_postmortem_template.html
```

Use `final/index.html` or read the numbered Markdown files in `final/`. The `final/` folder is intentionally clean: Markdown and plain HTML only, no YAML, CSV, or separate CSS files.

## How Updates Work

The skill treats every project as a workspace with explicit state:

```text
create stubs -> validate -> score -> ingest notes -> revalidate -> render outputs
```

It does not wait for a perfect brief. Empty files are created immediately and marked as `empty`, `partial`, `blocked`, `draft`, or `ready`.

Final recommendations stay blocked until the minimum gate is satisfied:

- offer;
- ICP or primary persona;
- target KPI;
- primary channel;
- proof assets or an explicit no-proof-yet flag.

## Language

The skill follows the user's conversation language for replies and generated files unless instructed otherwise. The agent should set this before creating the workspace, so the files are written in the right language immediately instead of being translated later.

## Manual CLI Usage

Most users should let the agent run these scripts. Use the commands below only for debugging, automation, or when your agent cannot execute local scripts.

<details>
<summary>Commands</summary>

Create a workspace:

```bash
python3 skills/designing-growth-funnels/scripts/create_workspace.py \
  --name "Acme onboarding funnel" \
  --out ./workspaces/acme-onboarding
```

Validate it:

```bash
python3 skills/designing-growth-funnels/scripts/validate_workspace.py \
  ./workspaces/acme-onboarding --json
```

Add rough notes:

```bash
python3 skills/designing-growth-funnels/scripts/ingest_notes.py \
  ./workspaces/acme-onboarding \
  --input ./notes/acme.txt
```

Render outputs:

```bash
python3 skills/designing-growth-funnels/scripts/render_outputs.py \
  ./workspaces/acme-onboarding
```

Open the visual summary:

```bash
open ./workspaces/acme-onboarding/final/index.html
```

</details>

## Scripts

| Script | Purpose |
| --- | --- |
| `create_workspace.py` | Creates every workspace file immediately. |
| `validate_workspace.py` | Updates `00_status.md` with scores, blockers, and warnings. |
| `ingest_notes.py` | Moves rough notes into YAML/CSV without deleting existing data. |
| `render_outputs.py` | Renders the raw artifacts and the clean `final/` pack. |

All scripts use only the Python standard library. No network calls. No secrets. No hidden dependencies.

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

Read third-party skills before installing them. This skill is intentionally conservative at runtime:

- Python standard library only;
- no network calls;
- no credential reads;
- no execution of user-provided code;
- writes only inside the workspace path passed to the scripts.

See [SECURITY.md](SECURITY.md).

## License

MIT.
