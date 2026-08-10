# pr-reviewer-demo

A small Flask task-tracker API used as a target repo for an AI-powered PR
reviewer. Each branch/PR in this repo intentionally introduces one realistic
issue (or, in one case, none) to exercise the reviewer bot: SQL injection,
missing auth, a hardcoded secret, an off-by-one edge case, and an N+1 query.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

## Test

```bash
pytest
```
