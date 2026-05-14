# Segmentation and Routing

Use this reference when assigning lead type, segment, or funnel skeleton.

## Routing dimensions

- `awareness`: unaware, problem-aware, solution-aware, product-aware, most-aware.
- `intent`: explore, diagnose, compare, start, buy, expand.
- `value_tier`: low, medium, high.
- `channel`: search, paid social, content/SEO, referral/partner, CRM/retargeting, sales-assisted.
- `persona_jtbd`: owner, operator, creator, buyer/procurement, admin/champion, existing customer.

## Default routing logic

```text
if lifecycle == existing_user:
    skeleton = expansion_rescue
elif persona == creator and monetization == recurring_access:
    skeleton = creator_subscription
elif value_tier == high or stakeholders_count > 1 or estimated_ttfv > 5:
    skeleton = demo_led
elif awareness in [product_aware, most_aware] and intent in [start, buy]:
    skeleton = direct_offer
elif self_serve_possible and estimated_ttfv <= 5:
    skeleton = trial_to_value
elif awareness in [problem_aware, solution_aware]:
    skeleton = diagnostic
else:
    skeleton = problem_aware
```

## Routing warnings

- High-value leads with long setup should not be forced into self-serve.
- Cold paid-social traffic usually needs problem framing before a hard checkout ask.
- Search and retargeting pages need tight message match.
- If unknown segment rate would exceed 5%, simplify routing rules.

