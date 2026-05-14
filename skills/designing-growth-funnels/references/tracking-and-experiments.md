# Tracking and Experiments

Use this reference when creating tracking plans, KPI contracts, or experiment cards.

## Event taxonomy

| Layer | Events | Required properties |
| --- | --- | --- |
| Acquisition | `Landing Viewed`, `CTA Clicked` | `channel`, `campaign_id`, `creative_id`, `keyword_or_audience`, `awareness_guess` |
| Routing | `Segment Assigned`, `Skeleton Selected` | `awareness`, `intent`, `value_tier`, `persona_id`, `skeleton_id`, `routing_version` |
| Brief | `Brief Started`, `Brief Question Answered`, `Brief Completed` | `question_id`, `branch_id`, `completion_time_seconds` |
| Diagnosis | `Diagnosis Generated`, `Roadmap Viewed` | `diagnosis_category`, `severity`, `confidence_score` |
| Onboarding | `Onboarding Started`, `Source Connected`, `First Value Reached` | `setup_path`, `integration_type`, `time_to_first_value_seconds`, `sample_data_used` |
| Monetization | `Trial Started`, `Paywall Viewed`, `Checkout Started`, `Payment Completed` | `plan_id`, `billing_period`, `price_local`, `discount`, `offer_type` |
| Retention | `Weekly Digest Opened`, `Action Pack Started`, `Week Return`, `Upgrade Completed` | `retention_recipe_id`, `health_score`, `expansion_signal`, `at_risk_flag` |
| Experimentation | `Experiment Exposed`, `Variant Assigned`, `Guardrail Breached` | `experiment_id`, `variant_id`, `holdout_id`, `exposure_time`, `eligibility_rule` |

## Experiment readiness

An experiment card needs:

- segment;
- skeleton;
- changed stage;
- hypothesis;
- primary metric;
- guardrail;
- traffic source;
- decision rule;
- data-quality checks.

Do not interpret results if SRM, exposure logging, or event loss is unresolved.

## Default decision rule

Ship only when:

- no data-quality flags;
- primary metric clears the practical threshold;
- guardrails do not degrade;
- qualitative evidence does not contradict the result;
- the operational complexity is justified.

