# Intake and Qualification

Use this when collecting context, scoring readiness, or deciding what to ask next.

## Required Minimum Gate

- `offer`: what is sold and what result it promises.
- `icp` or `primary_persona`: who the funnel is for.
- `target_kpi`: one metric the funnel should improve.
- `primary_channel`: where qualified traffic or leads come from.
- `proof_assets` or `explicit_no_proof_yet`: evidence state.

## Optional Inputs

- `jtbd`
- `pricing`
- `time_to_first_value_minutes`
- `sales_motion`
- `product_constraints`
- `unit_economics`
- `implementation_bandwidth`
- `experiment_bandwidth`

## Scoring

Qualification score uses 100 points:

- clear pain and promise: 20;
- proof assets: 10, or 3 when `explicit_no_proof_yet` is true;
- reachable channel and audience: 15;
- measurable path: 15;
- realistic first value: 15;
- plausible economics: 10;
- implementation bandwidth: 10;
- role and JTBD clarity: 5.

Default decision:

- `70+`: go to funnel build;
- `55-69`: strategy/research sprint;
- `<55`: no-go for growth build until proposition, proof, or measurement improves.

## Intake Behavior

Before the minimum gate is complete, write up to 3 prioritized questions into `next_best_input`, but ask the user only one question at a time in chat. Choose missing fields by impact:

1. target KPI;
2. offer;
3. ICP/persona;
4. primary channel;
5. proof/no-proof state.

After the minimum gate is complete, ask at most 2 clarify questions. They should be topic-specific and improve recommendation quality, not repeat the gate. Prioritize:

- priority segment for the next 14 days;
- current weak screen, bot step, email, or webinar step;
- main objection before the target action;
- first-value moment and time to first value;
- proof gap or strongest proof asset;
- owner and launch date for the first experiment.

Prefer rough input over waiting for perfect input. Mark assumptions clearly.

## Readiness

`minimum_gate_satisfied` means the agent has enough input to create a useful ready-to-test package. It does not mean the launch handoff is safe.

Use two readiness levels:

- `ready_to_test`: minimum gate is satisfied, contradictions are resolved, high-risk promises are not unresolved, and every recommendation has source or assumption coverage.
- `ready_for_launch`: no evidence gaps, no weak or missing proof, no unresolved reviewer approval, and no row-level launch blockers.

Recommendations can be ready to test when:

- the minimum gate is satisfied;
- recommendations use evidence refs or explicit `assumption_ids`;
- `no_proof` or `weak_proof` is low/medium risk and visibly assumption-backed;
- contradictions are resolved.

Launch handoff is ready only when:

- research readiness is at least 60;
- at least 3 sourced competitor rows are recorded;
- evidence gaps are resolved;
- proof and reviewer approval blockers are resolved.
