# Retention and Postmortem

Use this reference for retention loops, lifecycle paths, and experiment learning.

## Retention loop

Design retention as:

```text
trigger -> personalized insight -> one recommended action -> visible reward -> progress update
```

Good retention artifacts provide one new useful reason to return, not a generic reminder.

## Recipes

| Recipe | Trigger | Content | Reward | KPI |
| --- | --- | --- | --- | --- |
| Weekly benchmark digest | New week or new data | one change, one problem, one chance | new insight | digest open rate, week return |
| Improvement of the week | diagnosed gap | one ready action or template | quick win | `Action Pack Started` |
| Unfinished roadmap nudge | roadmap viewed, no next action | exact next step | recovered progress | route recovery rate |
| Success proof recap | first value reached | what worked plus next level | motivation | D7 retention |
| Expansion readiness | usage threshold | outcome-based upgrade | expanded value | upgrade click |
| Rescue loop | low activity | gap diagnosis plus restore path | return without friction | reactivation rate |

## Postmortem record

Every live test should end with:

- experiment or release ID;
- segment and skeleton;
- changed stage;
- hypothesis;
- change log;
- data-quality checks;
- results;
- qualitative evidence;
- root cause classification;
- decision: ship, hold, kill, or re-test;
- permanent learning;
- owner and due date.

Permanent learning should update a routing rule, screen pattern, scoring rule, or risk note.

