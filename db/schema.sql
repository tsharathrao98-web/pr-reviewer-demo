create table if not exists review_runs (
    id bigint generated always as identity primary key,
    repo text not null,
    pr_number int not null,
    status text not null check (status in ('completed', 'failed', 'skipped')),
    findings_count int not null default 0,
    severity_counts jsonb not null default '{}'::jsonb,
    category_counts jsonb not null default '{}'::jsonb,
    diff_truncated boolean not null default false,
    latency_ms int,
    input_tokens int,
    output_tokens int,
    model text,
    error text,
    created_at timestamptz not null default now()
);

create index if not exists review_runs_repo_pr_idx on review_runs (repo, pr_number);
create index if not exists review_runs_created_at_idx on review_runs (created_at);
