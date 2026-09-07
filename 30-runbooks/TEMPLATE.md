# Runbook TEMPLATE

Copy this file to `rb-<NNN>-<slug>.md` and fill it in.

```markdown
# RB-<NNN>: <Title>

**Risk level:** read-only | low | destructive
**Applies to:** dev-station / node-01 / node-02 / folder
**Prerequisites:** access works; latest backup if applicable

## When to use
<one or two lines>

## Procedure
1. <step — exact command>
2. …

## Verify success
<exact command + expected output>

## Rollback
<how to undo>

## Log
Append every step's result to `20-logs/command-log.md`; update `10-status/current-state.md`.
```
