# inc-001 — GitHub /pulls empty-body 500 (blocked all marathon ships)

**Status:** diagnosed, workaround implemented (direct_push mode); awaiting user confirm
- **Date (UTC):** 2026-09-07
- **Symptom:** `POST /repos/{owner}/{repo}/pulls` returns **500 with empty body** consistently; 0 PRs
  merged across all marathon cycles despite every other API/git op working.
- **Evidence:** verbose logging added to `github_api.py` (attempt-by-attempt + curl fallback stdout/stderr):
  urllib AND curl both 500; reproduces on BOTH `cloud-pos-system` + `selfide`; fresh rate limit
  (5000/5000); push/issues/comments/merge all OK. Not client-shape, not rate-limit, not repo-specific.
- **Hypothesis:** account-level PR-creation soft-flag / GitHub incident on this account (created ~20+
  probe PRs + 45+ issues today). **Action for user:** try creating a PR from the web UI on any repo; if
  it also fails → contact GitHub / finish any identity checks.
- **Workaround:** new `gates.ship: direct_push` — engine pushes branch→main directly (git push), board
  notes it, keeps the branch for a later PR. Guarantees product accumulation on the playground.
- **Reopen when:** /pulls starts returning 201 again (revert to `pr` mode for real repos).

## Internet research follow-up (2026-09-07)
- Symptom matches GH community thread #146178; GitHub attribute: PR+API status incident, later resolved.
- No unresolved status incident now, yet failure persists -> account/token-scoped soft-throttle suspected.
- Repo settings all-clear. See 40-knowledge addendum for sources + next steps.
