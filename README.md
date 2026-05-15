# Growth Funnel Skills

`designing-growth-funnels` is an Agent Skill that helps an AI agent build a practical, source-backed growth funnel strategy from rough business context.

The user asks for a funnel. The agent handles the internal workflow: it creates a workspace, normalizes the input, checks missing fields, tracks evidence, and renders a clean final report.

Repository: `saplq/growth-funnel-skills`

## What It Does

Use this skill when you need a growth funnel for:

- SaaS, subscriptions, marketplaces, services, real estate, education, creator products, or assisted-sales businesses;
- landing pages, Telegram/WhatsApp bots, webinars, onboarding, lead qualification, activation, paywalls, retention loops;
- source-backed competitor/research notes;
- tracking plans, experiment cards, and execution plans.

The final output is a human-readable package in `final/`:

- funnel blueprint;
- audience segmentation;
- screen / bot / webinar / onboarding specs;
- tracking plan;
- first experiment card;
- risks and gaps;
- execution plan.

## What It Does Not Do

- It does not browse the web inside bundled scripts.
- It does not invent proof, private metrics, pricing, benchmarks, or customer claims.
- It does not write to CRM, ad accounts, analytics, messengers, or external systems without explicit user approval.
- It does not replace strategy judgment; it structures the work and shows gaps clearly.

## Install

Skills are installed into an agent host, not into a model name. For example, you install it into Codex, ChatGPT Skills, Claude Code, Claude.ai, or another agent that supports `SKILL.md`.

<details>
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

Manual install:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
mkdir -p ~/.codex/skills
cp -R growth-funnel-skills/skills/designing-growth-funnels ~/.codex/skills/
```

</details>

<details>
<summary><strong>ChatGPT Skills</strong></summary>

Create a zip:

```bash
git clone https://github.com/saplq/growth-funnel-skills.git
cd growth-funnel-skills/skills
zip -r designing-growth-funnels.zip designing-growth-funnels
```

Upload in ChatGPT:

1. Open ChatGPT.
2. Open your profile menu.
3. Go to `Skills`.
4. Click `New skill`.
5. Choose `Upload from your computer`.
6. Upload `designing-growth-funnels.zip`.

Skills availability depends on your ChatGPT plan/workspace settings.

</details>

<details>
<summary><strong>Claude Code</strong></summary>

Personal install:

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
cd growth-funnel-skills/skills
zip -r designing-growth-funnels.zip designing-growth-funnels
```

Upload or attach the zipped skill folder using the Skills workflow available in your Claude.ai plan or Anthropic API setup.

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

Example:

```text
Use $designing-growth-funnels.

Собери маркетинговую growth funnel и финальный пакет на русском языке для девелоперской компании, которая продает недвижимость украинцам за границей.

Компания: NovaHabitat Development

Что продаем:
- квартиры и апартаменты в новых жилых комплексах;
- инвестиционные юниты под аренду;
- консультацию по покупке, оплате, налогам и сдаче в аренду.

Аудитория:
- украинцы в Европе, особенно Испания, Польша, Германия, Чехия, Португалия;
- предприниматели, IT-специалисты, семьи с капиталом от €80k;
- люди, которые хотят сохранить капитал, купить жилье для жизни или инвестировать в аренду.

Текущая воронка:
1. Собираем email-базу через партнеров, лид-магниты и прошлые мероприятия.
2. Из email-базы пытаемся дособрать номера телефонов.
3. Запускаем Meta Ads по украинцам в Европе.
4. Ведем трафик в Telegram bot.
5. Бот квалифицирует интерес: бюджет, страна, цель покупки, срок решения, нужен ли звонок.
6. Дальше ведем на вебинар или консультацию с менеджером.
7. После вебинара менеджер закрывает на подбор объекта и звонок с консультантом.

Primary channel: Meta Ads + email reactivation + Telegram bot + webinars.
Target KPI: Qualified consultation booked / Telegram bot started.

Current metrics:
- Meta lead cost: около €9-14 за старт Telegram bot.
- Bot started to qualified lead: примерно 18%.
- Webinar registration to attendance: примерно 32%.
- Consultation booked after webinar: примерно 9%.
- Sales cycle: от 2 недель до 4 месяцев.

Proof:
- уже продали 37 объектов украинским клиентам за последние 18 месяцев;
- есть 6 видео-отзывов клиентов;
- есть кейс семьи из Варшавы, которая купила апартамент в Испании для переезда;
- есть кейс инвестора из Праги, который купил юнит под аренду.

Constraints:
- сайт слабый, лучше сейчас не делать сложный редизайн;
- Telegram bot уже есть, но его можно переписать;
- команда может подготовить один вебинар в неделю;
- нужен запуск улучшенной воронки за 14 дней;
- нельзя обещать гарантированную доходность;
- важно не выглядеть как агрессивный инфобизнес.

Нужно:
- предложить сегментацию аудитории;
- выбрать структуру funnel;
- улучшить Telegram bot flow;
- предложить вебинарную механику;
- дать screen specs для landing/bot/webinar/consultation flow;
- дать tracking plan;
- дать experiment card для первого теста;
- указать risks, gaps и next step.
```

Expected agent behavior:

1. Create a workspace.
2. Ingest the user context.
3. Validate whether the minimum funnel gate is complete.
4. Render `final/index.html`.
5. Reply with the final path, scores, blockers, and next step.

## Minimum Input

The skill can start with rough notes, but final recommendations are blocked until these are known:

- offer;
- ICP or primary persona;
- target KPI;
- primary channel;
- proof assets or explicit `no proof yet`.

If something is missing, the agent should ask at most 3 short questions.

## How It Works Internally

The skill creates a workspace with two layers:

```text
funnel-workspace/
├── runtime/   # machine state, evidence, gaps, source registry
└── final/     # user-facing Markdown and self-contained HTML
```

`runtime/` is for the agent and audit trail. `final/` is for the user.

The bundled scripts are deterministic and offline:

- Python standard library only;
- no network calls;
- no credential reads;
- no execution of user-provided code;
- writes stay inside the selected workspace path.

## What The Final Pack Contains

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

## Methodology Basis

This skill combines practical growth, product analytics, UX measurement, and experimentation patterns. It is not based on one single proprietary framework.

Main influences:

- Funnel lifecycle thinking from AARRR / Pirate Metrics: acquisition, activation, retention, referral, revenue. See Dave McClure's [Startup Metrics for Pirates](https://www.slideshare.net/dmc500hats/startup-metrics-for-pirates-nov-2012).
- Customer motivation and positioning from Jobs To Be Done. See Harvard Business Review: [Know Your Customers' Jobs to Be Done](https://hbr.org/2016/09/know-your-customers-jobs-to-be-done).
- Product/UX measurement from Google's HEART framework. See Google Research: [Measuring the User Experience on a Large Scale](https://research.google.com/pubs/pub36299.html).
- Experiment design and guardrails from online controlled experimentation research. See Microsoft Research: [Online Experimentation at Microsoft](https://www.microsoft.com/en-us/research/?p=696748).
- Skill package structure from the Agent Skills / `SKILL.md` pattern used by OpenAI and Claude Code. See [OpenAI Skills in ChatGPT](https://help.openai.com/en/articles/20001066) and [Claude Code skills](https://code.claude.com/docs/en/skills).

How these ideas map into the skill:

- Minimum gate: prevents generic funnels when offer, audience, KPI, channel, or proof state is missing.
- Segmentation: separates ICP/persona, intent, geography, value tier, and buying stage.
- Funnel blueprint: chooses an appropriate path such as diagnostic-to-consultation, webinar-to-call, trial-to-value, or assisted-sales.
- Screen specs: tie every step to one target belief, one CTA, one primary metric, and one guardrail.
- Tracking plan: defines events before interpreting performance.
- Experiment card: forces hypothesis, segment, primary metric, guardrails, and decision rule.
- Provenance: current-practice, pricing, competitor, and research claims should carry source URL and retrieval date.

## Manual CLI Usage

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

Render final output:

```bash
python3 skills/designing-growth-funnels/scripts/render_final.py \
  ./workspaces/acme \
  --json
```

Open the final report:

```bash
open ./workspaces/acme/final/index.html
```

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
