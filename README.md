# Growth Funnel Skills

`designing-growth-funnels` is an Agent Skill that helps an AI agent build a practical, source-backed growth funnel strategy from rough business context.

The user asks for a funnel. The agent handles the internal workflow: it creates a workspace, normalizes the input, checks missing fields, tracks evidence, and renders a clean final report.

Repository: `saplq/growth-funnel-skills`

## Core Idea

This skill is built around one practical thesis: repeatable growth does not come from "creative marketing genius"; it comes from a system that rejects weak cases early, turns the work into measurable KPI contracts, gives users fast first value, instruments each step, and improves through experiments.

It does **not** promise 90%+ success for every product, audience, and traffic source. That would be dishonest. Instead, it is designed to make suitable projects more predictable by forcing this operating model:

```text
Fit Gate -> KPI Contract -> Journey Map -> First Value -> Instrumentation -> Experiment Loop -> Retention Loop -> Postmortem Library
```

In practice, the skill asks:

- Is this project ready for growth, or should it only get a diagnosis / strategy sprint?
- What one KPI defines success?
- What belief must change at each step of the funnel?
- Where does the user receive first value before or immediately after conversion?
- Which events prove that users moved forward?
- What is the first meaningful experiment?
- How does the product or funnel create a reason to return?
- What did the last result teach us for the next funnel?

## What It Does

Use this skill when you need a growth funnel for:

- SaaS, subscriptions, marketplaces, services, real estate, education, creator products, or assisted-sales businesses;
- landing pages, Telegram/WhatsApp bots, webinars, onboarding, lead qualification, activation, paywalls, retention loops;
- source-backed competitor/research notes;
- tracking plans, experiment cards, and execution plans.

The final output is a human-readable decision package in `final/`:

- decision summary and first action;
- audience segmentation and jobs;
- evidence-backed or assumption-backed recommendations;
- funnel map and screen / bot / webinar / onboarding playbook;
- tracking plan and first experiment;
- risks, gaps, and execution plan.

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

Quick template:

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

Expected agent behavior:

1. Create a workspace.
2. Ingest the user context.
3. Validate whether the minimum funnel gate is complete.
4. Compile `runtime/insights.json`.
5. Render `final/index.html`.
6. Reply with the final path, scores, blockers, and next step.

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
<summary><strong>Pet project / indie AI tool</strong></summary>

```text
Use $designing-growth-funnels.

Build a growth funnel and final report in English for an indie AI tool.

Project: ClipForge
Offer: turn long YouTube videos or podcasts into short clips, titles, captions, and posting ideas in under 5 minutes.
Audience: solo creators, small podcast teams, and newsletter writers who repurpose long-form content.
Primary channel: X/Twitter demos + Reddit communities + Product Hunt launch.
Target KPI: First clip exported / signup.
Current funnel: social demo post -> landing page -> free signup -> upload URL -> AI generates clips -> export -> paid upgrade.
Current metrics: waitlist 430 people, landing to waitlist 11%, demo post CTR about 3.2%, no paid users yet.
Proof: 37 beta users exported at least one clip, 9 users posted clips publicly, 4 testimonials from creators.
Constraints: solo builder, no paid ads, launch in 21 days, avoid making copyright or platform-policy claims.

Create positioning segments, launch funnel, activation flow, landing/onboarding specs, tracking plan, first experiment, risks, gaps, and next step.
```

</details>

<details>
<summary><strong>Pet project / consumer mobile app</strong></summary>

```text
Use $designing-growth-funnels.

Build a growth funnel and final report in English for a consumer mobile pet project.

Project: TinyHabits Garden
Offer: a lightweight habit tracker where each completed habit grows a small virtual garden.
Audience: students and young professionals who want a simple, friendly habit app without complex productivity systems.
Primary channel: TikTok organic videos + App Store search + friend invites.
Target KPI: D7 retained users / app install.
Current funnel: TikTok video -> App Store page -> install -> first habit created -> first 3-day streak -> invite a friend.
Current metrics: 1,200 installs, 54% create first habit, 21% reach a 3-day streak, D7 retention 12%.
Proof: 180 users completed at least 10 habits, 32 App Store reviews with 4.6 average rating.
Constraints: no backend engineer, small design budget, no paid ads, avoid manipulative streak mechanics.

Create user segments, activation and retention funnel, app screen specs, tracking plan, first experiment, risks, gaps, and next step.
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
<summary><strong>E-commerce / physical product</strong></summary>

```text
Use $designing-growth-funnels.

Build a growth funnel and final report in English for a direct-to-consumer e-commerce brand.

Brand: NomadBrew
Offer: compact travel coffee kit for remote workers, van-life travelers, and frequent flyers.
Audience: remote workers and travelers aged 25-45 who care about good coffee outside the home.
Primary channel: Meta Ads + TikTok organic + email capture.
Target KPI: Purchase completed / product page viewed.
Current funnel: short video ad -> product page -> bundle offer -> checkout -> post-purchase email -> review/referral.
Current metrics: product page conversion 2.1%, add-to-cart 7.8%, checkout completion 46%, AOV USD 74.
Proof: 1,800 units sold, 240 customer reviews, 4.7 average rating, UGC from travel creators.
Constraints: limited inventory for 6 weeks, shipping only to US/EU, avoid discount-heavy positioning.

Create segmentation, landing/product-page flow, offer structure, tracking plan, first experiment, risks, gaps, and next step.
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

<details>
<summary><strong>Nonprofit / community campaign</strong></summary>

```text
Use $designing-growth-funnels.

Build a growth funnel and final report in English for a nonprofit community campaign.

Organization: CityWarmth
Offer: help residents sponsor winter kits for newly arrived refugee families.
Audience: local residents, small businesses, churches, and community groups who want a concrete way to help.
Primary channel: local partnerships + Facebook groups + email newsletter + community events.
Target KPI: Sponsor signup completed / campaign page viewed.
Current funnel: partner post -> campaign page -> kit sponsorship form -> donation/payment -> thank-you email -> referral/share.
Current metrics: campaign page conversion 3.5%, average donation USD 58, email CTR 6.2%, referral share rate 8%.
Proof: 740 kits delivered last winter, photos from distribution events, partner endorsements from 12 local groups.
Constraints: protect beneficiary privacy, avoid guilt-based messaging, campaign runs for 30 days.

Create donor segments, campaign funnel, page/email specs, tracking plan, first experiment, risks, gaps, and next step.
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
├── runtime/   # machine state, evidence, gaps, source registry, insights
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
├── 00_index.md / 00_index.html              # start here
├── 01_status_next_steps.md / .html          # decision summary
├── 02_intake_brief.md / .html               # segments and jobs
├── 03_research_evidence.md / .html          # evidence and assumptions
├── 04_competitor_map.md / .html             # competitive patterns
├── 05_funnel_blueprint.md / .html           # funnel map
├── 06_screen_specs.md / .html               # screen playbook
├── 07_tracking_plan.md / .html              # tracking and KPIs
├── 08_experiment_card.md / .html            # next experiment
├── 09_risks_and_gaps.md / .html             # risks and gaps
└── 10_execution_plan.md / .html             # execution plan
```

## Methodology Basis

This skill combines practical growth, product analytics, UX measurement, and experimentation patterns. It is not based on one single proprietary framework.

Main influences:

- Funnel lifecycle thinking from AARRR / Pirate Metrics: acquisition, activation, retention, referral, revenue. See Dave McClure's [Startup Metrics for Pirates](https://www.slideshare.net/dmc500hats/startup-metrics-for-pirates-nov-2012).
- Customer motivation and positioning from Jobs To Be Done. See Harvard Business Review: [Know Your Customers' Jobs to Be Done](https://hbr.org/2016/09/know-your-customers-jobs-to-be-done).
- Product/UX measurement from Google's HEART framework. See Google Research: [Measuring the User Experience on a Large Scale](https://research.google.com/pubs/pub36299.html).
- Experiment design and guardrails from online controlled experimentation research. See Microsoft Research: [Online Experimentation at Microsoft](https://www.microsoft.com/en-us/research/?p=696748).
- Iterative usability testing from Nielsen Norman Group's small-batch testing guidance. See [Why You Only Need to Test with 5 Users](https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/).
- Compounding growth systems from growth-loop thinking. See Reforge: [The One Growth Metric that Moves Acquisition, Monetization, and Virality](https://www.reforge.com/blog/growth-metric-acquisition-monetization-virality).
- Skill package structure from the Agent Skills / `SKILL.md` pattern used by OpenAI and Claude Code. See [OpenAI Skills in ChatGPT](https://help.openai.com/en/articles/20001066) and [Claude Code skills](https://code.claude.com/docs/en/skills).

How these ideas map into the skill:

- Minimum gate: prevents generic funnels when offer, audience, KPI, channel, or proof state is missing.
- KPI contract: replaces vague goals like "more clients" with one measurable success target.
- Segmentation: separates ICP/persona, intent, geography, value tier, and buying stage.
- Funnel blueprint: chooses an appropriate path such as diagnostic-to-consultation, webinar-to-call, trial-to-value, or assisted-sales.
- Belief shifts and screen specs: tie every step to one target belief, one CTA, one primary metric, and one guardrail.
- First value: pushes the funnel to show a useful preview or result before asking for deeper commitment.
- Tracking plan: defines events before interpreting performance.
- Experiment card: forces hypothesis, segment, primary metric, guardrails, and decision rule.
- Retention loop: makes the funnel continue after payment, signup, or consultation.
- Postmortem habit: turns failed tests into reusable rules and stronger patterns.
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
