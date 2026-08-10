# CLAUDE.md

## What this repo is

A small Flask task-tracker API used as the target for an AI PR-review bot
(`.github/workflows/pr-review.yml` + `scripts/review_pr.py`). Branches/PRs on
this repo intentionally seed one issue each so the bot has something real to
catch.

## Review bot rubric (scripts/review_pr.py)

The bot only flags: SQL/command injection, missing auth/authz checks,
hardcoded secrets, off-by-one/edge-case correctness bugs, and N+1 query /
missing-batching performance issues. It does not flag style or naming — keep
it that way. Expanding the rubric means expanding `REVIEW_TOOL`'s `category`
enum *and* the system prompt's bullet list together, or the model will
silently invent categories outside the schema.

## Non-negotiables

- The bot is comment-only (`event: "COMMENT"`), never `REQUEST_CHANGES`, and
  never auto-merges. Human review is still required before merge — don't
  change this without discussing it first.
- On any failure (API error, malformed response, rate limit), the script
  posts a neutral fallback comment and exits 0. It must never fail the check
  in a way that blocks merging — this is an advisory tool, not a gate.
- All GitHub writes go through the two functions in `review_pr.py`
  (`post_review`, `post_fallback_comment`). Don't add a third path.

## Known limitations (intentional v1 scope cuts)

- Single review-body comment, not inline per-line comments — line-position
  mapping against multi-hunk diffs was cut for time; revisit if this becomes
  the actual product.
- Diffs over ~60k characters are truncated, not chunked. Large PRs get
  partial coverage. This is flagged in the comment body, not hidden.
- No feedback loop (👍/👎 on findings) yet — the rubric doesn't improve from
  usage. Static prompt, will drift as false positives accumulate.
- No cost ceiling or kill switch. Fine for a personal repo, not fine at
  organization scale.
