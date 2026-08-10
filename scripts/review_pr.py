import json
import os
import subprocess
import sys
import time

import requests
from anthropic import Anthropic

MODEL = os.environ.get("REVIEW_MODEL", "claude-sonnet-5")
MAX_DIFF_CHARS = 60_000

REVIEW_TOOL = {
    "name": "submit_review",
    "description": "Submit structured code review findings for this pull request diff.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "1-3 sentence overall assessment of the PR.",
            },
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "line": {"type": "integer"},
                        "severity": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "injection",
                                "broken-auth",
                                "sensitive-data-exposure",
                                "secrets",
                                "correctness",
                                "performance",
                                "other",
                            ],
                        },
                        "issue": {"type": "string"},
                        "recommendation": {"type": "string"},
                    },
                    "required": ["file", "severity", "category", "issue", "recommendation"],
                },
            },
        },
        "required": ["summary", "findings"],
    },
}

SYSTEM_PROMPT = """You are a senior code reviewer. Review the given pull request diff for:
- OWASP-style security issues: injection (SQL/command/etc.), broken auth/missing authz checks,
  hardcoded secrets/credentials, sensitive data exposure.
- Correctness bugs: off-by-one errors, unhandled edge cases, incorrect boundary conditions.
- Performance issues: N+1 queries, unnecessary loops over I/O, missing batching.

Only report issues you can point to a specific file and line for. Do not invent line numbers.
If the diff has no issues, return an empty findings list and say so in the summary.
Be concise. Do not flag style preferences or nitpicks that aren't correctness, security, or
performance issues."""


def log(event, **fields):
    print(json.dumps({"event": event, **fields}), flush=True)


def get_diff(base_sha, head_sha):
    diff = subprocess.run(
        ["git", "diff", f"{base_sha}...{head_sha}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    truncated = len(diff) > MAX_DIFF_CHARS
    if truncated:
        diff = diff[:MAX_DIFF_CHARS]
    return diff, truncated


def run_review(diff):
    client = Anthropic()
    started = time.time()
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "submit_review"},
        messages=[{"role": "user", "content": f"Review this diff:\n\n{diff}"}],
    )
    latency_ms = int((time.time() - started) * 1000)
    tool_use = next(b for b in resp.content if b.type == "tool_use")
    meta = {
        "latency_ms": latency_ms,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "model": MODEL,
    }
    return tool_use.input, meta


def format_body(review, truncated):
    lines = [review["summary"], ""]
    if truncated:
        lines.append(
            "_Note: this diff was truncated for review — large PRs are not fully covered yet._"
        )
        lines.append("")

    findings = review.get("findings", [])
    if not findings:
        lines.append("No issues found.")
    else:
        severity_emoji = {"high": "\U0001f534", "medium": "\U0001f7e1", "low": "⚪"}
        for f in findings:
            loc = f"`{f['file']}`" + (f":{f['line']}" if f.get("line") else "")
            lines.append(
                f"{severity_emoji.get(f['severity'], '⚪')} **{f['category']}** — {loc}\n"
                f"{f['issue']}\n"
                f"*Suggestion:* {f['recommendation']}\n"
            )

    lines.append("\n---\n_Automated review — human review still required before merge._")
    return "\n".join(lines)


def post_review(repo, pr_number, token, body):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}/reviews"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        json={"body": body, "event": "COMMENT"},
        timeout=10,
    )
    resp.raise_for_status()


def post_fallback_comment(repo, pr_number, token, message):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    try:
        requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"body": message},
            timeout=10,
        )
    except Exception as e:
        log("fallback_comment_failed", error=str(e))


def main():
    repo = os.environ["REPO"]
    pr_number = os.environ["PR_NUMBER"]
    base_sha = os.environ["BASE_SHA"]
    head_sha = os.environ["HEAD_SHA"]
    token = os.environ["GITHUB_TOKEN"]

    try:
        diff, truncated = get_diff(base_sha, head_sha)
        if not diff.strip():
            log("review_skipped", reason="empty_diff", pr=pr_number)
            return

        review, meta = run_review(diff)
        findings = review.get("findings", [])
        severity_counts = {}
        for f in findings:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1

        body = format_body(review, truncated)
        post_review(repo, pr_number, token, body)

        log(
            "review_completed",
            pr=pr_number,
            repo=repo,
            findings_count=len(findings),
            severity_counts=severity_counts,
            diff_truncated=truncated,
            **meta,
        )
    except Exception as e:
        log("review_failed", pr=pr_number, repo=repo, error=str(e))
        post_fallback_comment(
            repo,
            pr_number,
            token,
            "_AI review skipped due to an internal error. See Action logs. Human review still required._",
        )
        # Informational tool only — never fail the check in a way that blocks merging.
        sys.exit(0)


if __name__ == "__main__":
    main()
