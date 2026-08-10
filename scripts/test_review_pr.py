from review_pr import format_body


def test_format_body_no_findings():
    review = {"summary": "Looks good, no issues found.", "findings": []}
    body = format_body(review, truncated=False)
    assert "Looks good" in body
    assert "No issues found." in body


def test_format_body_with_findings():
    review = {
        "summary": "One issue found.",
        "findings": [
            {
                "file": "app.py",
                "line": 42,
                "severity": "high",
                "category": "injection",
                "issue": "Query built via f-string.",
                "recommendation": "Use a parameterized query.",
            }
        ],
    }
    body = format_body(review, truncated=False)
    assert "`app.py`:42" in body
    assert "injection" in body
    assert "parameterized query" in body


def test_format_body_flags_truncation():
    review = {"summary": "Reviewed the first part of a large diff.", "findings": []}
    body = format_body(review, truncated=True)
    assert "truncated" in body
