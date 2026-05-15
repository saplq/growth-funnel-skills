# Release Checklist

## Skill Package

- `SKILL.md` has valid frontmatter with `name` and `description`.
- Description front-loads trigger keywords and scope boundaries.
- `agents/openai.yaml` matches the skill.
- References are focused and directly linked from `SKILL.md`.
- Scripts have `--help`, clear errors, and JSON stdout.

## Workspace

- `runtime/` contains all machine state.
- `final/` contains only Markdown and HTML.
- Re-rendering is idempotent.
- Existing workspaces can be validated without data loss.

## Security

- No network calls in scripts.
- No environment secret reads.
- No user-provided code execution.
- User notes are data, not instructions.
- External writes require user approval.

## Verification

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q skills/designing-growth-funnels/scripts tests
```

Run skill validation if available:

```bash
python3 /path/to/quick_validate.py skills/designing-growth-funnels
```

## Distribution

- README install commands are current.
- Manual install path works for Codex and Claude-style agents.
- Zip packaging from `skills/` contains only the skill folder.
