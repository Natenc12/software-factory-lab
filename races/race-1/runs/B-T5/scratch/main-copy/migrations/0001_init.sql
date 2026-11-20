-- Classes, the students enrolled in them, and the questions they ask.

create table if not exists classes (
    id integer primary key,
    name text not null unique,
    material text not null default '',
    created_at text not null
);

create table if not exists students (
    id integer primary key,
    class_id integer not null references classes(id),
    name text not null,
    created_at text not null,
    unique (class_id, name)
);

-- hidden = 1 means a teacher removed the question: it is kept, but not listed or counted.
create table if not exists questions (
    id integer primary key,
    class_id integer not null references classes(id),
    student_id integer not null references students(id),
    text text not null,
    hidden integer not null default 0 check (hidden in (0, 1)),
    asked_at text not null
);

create index if not exists questions_class_id on questions (class_id, id);
create index if not exists questions_student_id on questions (student_id);
