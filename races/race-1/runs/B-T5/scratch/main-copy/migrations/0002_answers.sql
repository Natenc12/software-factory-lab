-- Answers to questions, and the small job table used to answer them in the background.

create table if not exists answers (
    id integer primary key,
    question_id integer not null unique references questions(id),
    body text not null,
    provider text not null,
    created_at text not null
);

-- status: pending -> running -> done | failed
create table if not exists jobs (
    id integer primary key,
    kind text not null,
    payload text not null default '{}',
    status text not null default 'pending'
        check (status in ('pending', 'running', 'done', 'failed')),
    attempts integer not null default 0,
    error text,
    created_at text not null,
    updated_at text not null
);

create index if not exists jobs_status on jobs (status, id);
