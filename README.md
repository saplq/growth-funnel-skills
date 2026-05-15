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

Build a marketing growth funnel and final report in English for this business.

Company: NovaHabitat Development

Offer:
We sell new-build apartments and investment units to Ukrainian buyers living in Europe. The service includes property selection, purchase guidance, payment process, tax basics, and rental setup support.

Audience:
- Ukrainians living in Europe, especially Spain, Poland, Germany, Czech Republic, and Portugal.
- Entrepreneurs, IT specialists, and families with available capital from EUR 80k.
- Buyers who want to preserve capital, relocate, or buy a rental property.

Current funnel:
1. We collect an email database through partners, lead magnets, and past webinars.
2. We try to enrich email contacts with phone numbers.
3. We run Meta Ads targeting Ukrainians in Europe.
4. Traffic goes to a Telegram bot.
5. The bot qualifies budget, preferred country, buying goal, decision timing, and whether the person wants a call.
6. Qualified leads go to a webinar or a manager consultation.
7. After the webinar, sales managers try to book a property selection call.

Primary channel: Meta Ads + email reactivation + Telegram bot + webinars.
Target KPI: Qualified consultation booked / Telegram bot started.

Current metrics:
- Meta cost per Telegram bot start: about EUR 9-14.
- Bot started to qualified lead: about 18%.
- Webinar registration to attendance: about 32%.
- Consultation booked after webinar: about 9%.
- Sales cycle: 2 weeks to 4 months.

Proof:
- 37 properties sold to Ukrainian clients in the last 18 months.
- 6 client video testimonials.
- One case study from a family in Warsaw buying an apartment in Spain for relocation.
- One case study from a Prague-based investor buying a rental unit.

Constraints:
- The current website is weak, so avoid a heavy website redesign for now.
- Telegram bot already exists and can be rewritten.
- The team can prepare one webinar per week.
- Improved funnel should launch in 14 days.
- We cannot promise guaranteed investment returns.
- The tone must feel premium and trustworthy, not aggressive or infobusiness-like.

Please produce:
- audience segmentation;
- funnel structure;
- improved Telegram bot flow;
- webinar mechanism;
- screen specs for landing / bot / webinar / consultation flow;
- tracking plan;
- first experiment card;
- risks, gaps, and next step.
```

Expected agent behavior:

1. Create a workspace.
2. Ingest the user context.
3. Validate whether the minimum funnel gate is complete.
4. Render `final/index.html`.
5. Reply with the final path, scores, blockers, and next step.

## Example Prompts By Niche

Use these as starting points. Replace the details with your own business.

<details>
<summary><strong>Real estate developer / property sales</strong></summary>

```text
Use $designing-growth-funnels.

Build a marketing growth funnel and final report in English for a real estate developer selling new-build apartments to Ukrainian buyers living in Europe.

Company: NovaHabitat Development
Offer: property selection, purchase guidance, payment process, tax basics, and rental setup support for buyers interested in Spain, Maldives, and Zanzibar.
Audience: Ukrainian entrepreneurs, IT specialists, and families living in Europe with available capital from EUR 80k.
Primary channel: Meta Ads + email reactivation + Telegram bot + webinars.
Target KPI: Qualified consultation booked / Telegram bot started.
Current funnel: email database -> phone enrichment -> Meta Ads -> Telegram bot -> webinar or manager consultation -> property selection call.
Current metrics: EUR 9-14 per bot start, 18% bot start to qualified lead, 32% webinar attendance, 9% consultation booked after webinar.
Proof: 37 properties sold in 18 months, 6 video testimonials, two client case studies.
Constraints: launch improved funnel in 14 days, avoid heavy website redesign, no guaranteed-return claims, premium trustworthy tone.

Create segmentation, funnel structure, Telegram bot flow, webinar mechanism, screen specs, tracking plan, first experiment card, risks, gaps, and next step.
```

</details>

<details>
<summary><strong>SaaS / product-led growth</strong></summary>

```text
Use $designing-growth-funnels.

Build a source-backed growth funnel and final report in English for a B2B SaaS product.

Company: SignalDesk
Offer: connect Stripe and CRM to see churn risks and a list of accounts to win back this week.
Audience: B2B SaaS founders and operators with MRR from USD 20k to USD 300k.
Primary channel: LinkedIn outbound + content-led landing page.
Target KPI: First Value Reached / Trial Started.
Current funnel: content post -> landing page -> trial signup -> Stripe/CRM connection -> churn risk dashboard -> upgrade.
Current metrics: landing to signup 4.8%, trial activation 27%, time to first value about 5 minutes.
Proof: pilot cohort of 12 SaaS teams found an average of 18% high-risk accounts in week one.
Constraints: one frontend engineer, one growth marketer, first experiment should launch in 10 days.

Create segmentation, funnel blueprint, onboarding screens, tracking plan, first experiment card, risks, gaps, and execution plan.
```

</details>

<details>
<summary><strong>Telegram bot / webinar funnel</strong></summary>

```text
Use $designing-growth-funnels.

Build a Telegram bot and webinar growth funnel in English.

Business: expert-led education company selling a high-ticket online program.
Offer: 8-week program helping Ukrainian entrepreneurs in Europe systemize sales and launch Meta Ads.
Audience: Ukrainian small business owners in Poland, Germany, Spain, and Czech Republic.
Primary channel: Meta Ads to Telegram bot, email reactivation, weekly webinar.
Target KPI: Paid strategy call booked / Telegram bot started.
Current funnel: ad -> Telegram bot quiz -> webinar registration -> webinar attendance -> strategy call -> payment.
Current metrics: EUR 6 per bot start, 22% bot completion, 38% webinar attendance, 7% call booking after webinar.
Proof: 120 graduates, 14 video testimonials, 3 public case studies.
Constraints: avoid exaggerated income claims, keep compliance-safe ad messaging, launch in 7 days.

Create audience segments, bot questions, webinar structure, CTA sequence, screen specs, tracking plan, first experiment, risks, and next step.
```

</details>

<details>
<summary><strong>Marketplace</strong></summary>

```text
Use $designing-growth-funnels.

Build a growth funnel and final report in English for a two-sided marketplace.

Company: CareMatch
Offer: match families with verified home-care providers within 48 hours.
Audience: adult children looking for care for parents; providers are licensed caregivers and small agencies.
Primary channel: Google Search + local partnerships + retargeting.
Target KPI: Matched consultation booked / qualified request submitted.
Current funnel: search ad -> landing page -> care request form -> provider shortlist -> consultation call.
Current metrics: landing conversion 6%, qualified request rate 41%, provider response rate 62%.
Proof: 420 completed matches, average provider rating 4.7/5, two local partner endorsements.
Constraints: trust and safety are critical, avoid medical claims, support team can manually review 50 requests per week.

Create demand-side and supply-side segmentation, funnel blueprint, screen specs, tracking plan, first experiment, risks, and execution plan.
```

</details>

<details>
<summary><strong>Local service business</strong></summary>

```text
Use $designing-growth-funnels.

Build a practical growth funnel and final report in English for a local service business.

Business: premium dental clinic in Barcelona.
Offer: implant consultation and treatment planning for expats.
Audience: English-speaking and Ukrainian-speaking expats aged 35-65 in Barcelona and nearby areas.
Primary channel: Google Search + Meta retargeting + WhatsApp follow-up.
Target KPI: Consultation booked / qualified lead submitted.
Current funnel: Google ad -> landing page -> WhatsApp or form -> coordinator call -> clinic consultation.
Current metrics: EUR 28 per lead, 45% lead to coordinator call, 31% coordinator call to clinic consultation.
Proof: 12 years in business, 900+ implant cases, doctor credentials, patient reviews.
Constraints: healthcare compliance, no unrealistic outcome promises, clinic has limited consultation slots.

Create segmentation, landing/WhatsApp flow, trust proof plan, tracking plan, first experiment, risks, and next step.
```

</details>

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
