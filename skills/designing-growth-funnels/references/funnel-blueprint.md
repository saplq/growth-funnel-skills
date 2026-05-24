# Funnel Blueprint

Use this for segmentation, skeleton selection, and screen specs.

## Segmentation Axes

- Awareness: unaware, problem-aware, solution-aware, product-aware.
- Intent: learning, evaluating, switching, urgent.
- Value tier: low, mid, high, enterprise.
- Sales motion: self-serve, product-led sales, sales-assisted, enterprise.
- Time to first value: immediate, short, long.

## Default Skeletons

- `trial_to_value`: user can reach value quickly after signup.
- `diagnostic_to_roadmap`: value comes from assessment and prioritized plan.
- `demo_led`: high value, longer setup, or enterprise trust requirement.
- `lead_magnet_to_consult`: education-first funnel with assisted close.
- `template_to_activation`: user starts from a reusable artifact.
- `community_to_offer`: audience-led funnel.
- `retention_loop`: returning value and expansion path.

## Screen Spec Fields

Each screen should define:

- stage;
- target belief;
- content promise;
- primary CTA;
- microcopy;
- primary metric;
- guardrail;
- proof needed;
- blocked assumptions.
- support evidence or assumption id.
- evidence mode: source-backed or assumption-backed.

## Recommendation Rule

Keep each stage tied to one target belief, one CTA, one primary metric, one guardrail, and one support reference. If the minimum gate is missing, mark recommendations blocked instead of filling gaps with generic copy.

Variant bundles should stay compact: 2-3 copy, action, route, proof-placement, or qualification changes with hypothesis, target segment, measurement event, proof requirement, and the same claim/source/assumption coverage as the parent recommendation. Assumption-backed variants can be ready to test, but their launch exports must stay blocked.

Render a visual funnel map from the same screen specs. Highlight assumption-backed steps so the user sees what can be tested now and what still blocks launch handoff.
